"""Monthly import of data exported straight from the SATE system (سامانه ساتع).

One entry point for the four registries exported from the SATE grids:

    data/Add_In/Addin_Researchers.xlsx   فناوران   (also creates companies /
                                                    institutes as universities)
    data/Add_In/Addin_Demands.xlsx       تقاضاها / فراخوان‌ها
    data/Add_In/Addin_Proposals.xlsx     پیشنهاده‌ها
    data/Add_In/Addin_Contracts.xlsx     قراردادها
    data/Add_In/Addin_Universities.xlsx  (اختیاری) دانشگاه‌ها / موسسات

Files that are not present are simply skipped. Each file is the raw
"Export" of the corresponding SATE grid (first worksheet, original Persian
headers) -- no manual editing needed.

Matching / de-duplication (every record is matched BEFORE anything is
written -- re-running the same files is safe and imports nothing twice):

* researchers : national code (leading zeros ignored; for a legal-entity
  registration the representative's «کد ملی نماینده» is the researcher and
  the entity's شناسه ملی becomes a University row, exactly like the data
  already in the database).
* universities: شناسه ملی (leading zeros ignored).
* demands     : کد رهگیری.
* proposals   : کد رهگیری (= proposals.id).
* contracts   : کد رهگیری.

Existing records are NEVER overwritten (manual corrections stay intact).
Two exceptions that are real updates, not corrections: a proposal's
status (e.g. «در انتظار تایید متقاضی» -> «تایید نهایی») and blank links of
an existing proposal (demand / researcher / university). Everything else
that differs from the database is only listed in the report.

Rows that cannot be linked (unknown employer, university, researcher ...)
are not imported; they are listed with the reason in the report so the
missing master data can be added and the same file re-run.

Order inside one run: universities -> researchers -> demands -> proposals
-> contracts (each step sees what the previous one just added).

Usage
-----
    python scripts/import_satec_addin.py             # import
    python scripts/import_satec_addin.py --dry-run   # report only, no write
    python scripts/import_satec_addin.py --only contracts,demands
    python scripts/import_satec_addin.py --dir D:\\other\\folder

The report is written to results/import_reports/addin_import_<time>.xlsx.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.database import SessionLocal  # noqa: E402
from core.date_helper import parse_strict_jalali_date  # noqa: E402
import models.transfer  # noqa: E402,F401  (mapper registry)
from models.contract import Contract  # noqa: E402
from models.demand import Demand  # noqa: E402
from models.employer import Employer  # noqa: E402
from models.proposal import Proposal  # noqa: E402
from models.researchers import Researcher  # noqa: E402
from models.university import University  # noqa: E402

DEFAULT_DIR = PROJECT_ROOT / "data" / "Add_In"
REPORT_DIR = PROJECT_ROOT / "results" / "import_reports"

FILE_NAMES = {
    "universities": "Addin_Universities.xlsx",
    "researchers": "Addin_Researchers.xlsx",
    "demands": "Addin_Demands.xlsx",
    "proposals": "Addin_Proposals.xlsx",
    "contracts": "Addin_Contracts.xlsx",
}
STEP_ORDER = ["universities", "researchers", "demands", "proposals", "contracts"]

ALLOWED_CONTRACT_EMPLOYER_TYPES = {"Mother", "Independent"}
NATIONAL_CODE_LENGTH = 10

REG_TYPE_LEGAL_PREFIX = "شخص حقوقی"
REG_TYPE_EMPLOYER = "شرکت های مشمول"
REG_TYPE_FACULTY = "عضو هیات علمی"

RESEARCHER_TYPE_FACULTY = "عضو هیئت علمی"
RESEARCHER_TYPE_TECHNOLOGIST = "فناور"
DEFAULT_PROVINCE = "نامشخص"
DEFAULT_UNIVERSITY_STATUS = "فعال"

# ---------------------------------------------------------------- helpers

_CHAR_MAP = str.maketrans({
    "ي": "ی", "ى": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه",
    "\u200c": " ", "\u200f": "", "\u200e": "", "ـ": "",
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
    "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
})
_UNI_PREFIX = "دانشگاه "


def norm(text: Any) -> str:
    """Spacing/character-variant-insensitive form of a Persian name."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    value = str(text).translate(_CHAR_MAP)
    return re.sub(r"\s+", " ", value).strip()


def compact(text: Any) -> str:
    return norm(text).replace(" ", "")


def clean(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text.lower() in ("nan", "none", ""):
        return None
    return text[:-2] if text.endswith(".0") else text


def digits(value: Any) -> str | None:
    text = clean(value)
    if text is None:
        return None
    text = text.translate(_CHAR_MAP)
    return text if text.isdigit() else None


def code_key(code: str | None) -> str | None:
    """Comparison key for a national code: leading zeros are ignored."""
    return code.lstrip("0") if code else None


def pad_national_code(code: str) -> str:
    return code.zfill(NATIONAL_CODE_LENGTH) if len(code) < NATIONAL_CODE_LENGTH else code


def read_sheet(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=0, dtype=str, engine="openpyxl")


def jalali_to_date(value: Any):
    text = clean(value)
    if text is None:
        return None
    return parse_strict_jalali_date(text)


class NameIndex:
    """name -> value lookup tolerant of ی/ک, ZWNJ and spacing variants.

    Tiers: exact (stripped) -> normalized -> compact (no spaces) ->
    (optional) without a leading «دانشگاه ». A tier only answers when it
    points at exactly one record, so an ambiguous name is never guessed.
    """

    def __init__(self, strip_university_prefix: bool = False,
                 filler_words: frozenset[str] | None = None) -> None:
        self.strip_prefix = strip_university_prefix
        self.filler = filler_words
        self.exact: dict[str, set] = defaultdict(set)
        self.normed: dict[str, set] = defaultdict(set)
        self.compacted: dict[str, set] = defaultdict(set)
        self.no_prefix: dict[str, set] = defaultdict(set)
        self.core: dict[str, set] = defaultdict(set)

    def _core(self, text: str) -> str:
        words = [w for w in norm(text).split(" ") if w and w not in (self.filler or ())]
        return "".join(words)

    def _prefixless(self, text: str) -> str:
        n = norm(text)
        return compact(n[len(_UNI_PREFIX):]) if n.startswith(_UNI_PREFIX) else compact(n)

    def add(self, name: str | None, value: Any) -> None:
        if not name:
            return
        self.exact[name.strip()].add(value)
        self.normed[norm(name)].add(value)
        self.compacted[compact(name)].add(value)
        if self.strip_prefix:
            self.no_prefix[self._prefixless(name)].add(value)
        if self.filler:
            self.core[self._core(name)].add(value)

    def get_ex(self, name: str | None) -> tuple[Any, bool]:
        """(value, exact) -- ``exact`` is False for the approximate tiers
        (university prefix / filler words dropped)."""
        if not name:
            return None, True
        tiers = [
            (self.exact, name.strip(), True),
            (self.normed, norm(name), True),
            (self.compacted, compact(name), True),
        ]
        if self.strip_prefix:
            tiers.append((self.no_prefix, self._prefixless(name), False))
        if self.filler:
            tiers.append((self.core, self._core(name), False))
        for table, key, exact in tiers:
            hits = table.get(key)
            if hits and len(hits) == 1:
                return next(iter(hits)), exact
        return None, True

    def get(self, name: str | None):
        return self.get_ex(name)[0]


class Report:
    def __init__(self) -> None:
        self.new: list[dict] = []
        self.todo: list[dict] = []
        self.diff: list[dict] = []
        self.counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def count(self, table: str, key: str, n: int = 1) -> None:
        self.counts[table][key] += n

    def add_new(self, table: str, code: Any, name: Any, note: str = "") -> None:
        self.new.append({"جدول": table, "کد": code, "نام/عنوان": name, "توضیح": note})

    def add_todo(self, table: str, code: Any, name: Any, reason: str, value: Any = "") -> None:
        self.todo.append({
            "جدول": table, "کد": code, "نام/عنوان": name,
            "علت (وارد نشد)": reason, "مقدار مسئله‌دار": value,
        })

    def add_diff(self, table: str, code: Any, field: str, db_value: Any, file_value: Any,
                 applied: bool = False) -> None:
        self.diff.append({
            "جدول": table, "کد": code, "فیلد": field,
            "مقدار در پایگاه داده": db_value, "مقدار در فایل": file_value,
            "اعمال شد؟": "بله" if applied else "خیر (فقط گزارش)",
        })

    def summary_rows(self) -> list[dict]:
        labels = {
            "read": "ردیف خوانده‌شده از فایل",
            "inserted": "رکورد جدید واردشده",
            "existing": "از قبل موجود (تکراری، رد شد)",
            "updated": "به‌روزرسانی (وضعیت/لینک)",
            "unresolved": "وارد نشد (نیازمند اقدام)",
            "skipped": "ردشده (غیرمرتبط/تکراری در فایل)",
        }
        rows = []
        for table, stats in self.counts.items():
            row = {"جدول": table}
            for key, label in labels.items():
                row[label] = stats.get(key, 0)
            rows.append(row)
        return rows

    def save(self, path: Path, dry_run: bool) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            pd.DataFrame(self.summary_rows()).to_excel(writer, sheet_name="خلاصه", index=False)
            pd.DataFrame(self.new or [{"جدول": "-"}]).to_excel(writer, sheet_name="رکوردهای جدید", index=False)
            pd.DataFrame(self.todo or [{"جدول": "-"}]).to_excel(writer, sheet_name="وارد نشد - نیازمند اقدام", index=False)
            pd.DataFrame(self.diff or [{"جدول": "-"}]).to_excel(writer, sheet_name="تفاوت با پایگاه داده", index=False)
            for ws in writer.book.worksheets:
                ws.sheet_view.rightToLeft = True
                for col in ws.columns:
                    width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:200])
                    ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 10), 60)
        print(f"\nگزارش ذخیره شد{' (dry-run)' if dry_run else ''}: {path}")


# --------------------------------------------------------- universities

def _university_type_from_name(name: str) -> str:
    n = norm(name)
    if n.startswith("دانشگاه") or "دانشگاه" in n.split(" ")[:2]:
        return "دانشگاه"
    if n.startswith("پژوهشگاه") or n.startswith("پژوهشکده"):
        return "پژوهشگاه"
    if n.startswith("پارک"):
        return "پارک علم و فناوری"
    if n.startswith("موسسه") or n.startswith("مؤسسه"):
        return "موسسه آموزشی"
    if n.startswith("شرکت"):
        return "شرکت دانش بنیان"
    return "نامشخص"


class UniversityStore:
    """Active universities: by national id (zeros ignored) and by name."""

    def __init__(self, db) -> None:
        self.by_key: dict[str, University] = {}
        self.names = NameIndex(strip_university_prefix=True)
        self.city_province: dict[str, str] = {}
        province_votes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for u in db.query(University).all():
            self.by_key[code_key(u.national_id)] = u
            if not u.is_deleted:
                self.names.add(u.name, u.national_id)
            if u.city and u.province and u.province != DEFAULT_PROVINCE:
                province_votes[norm(u.city)][u.province] += 1
        for city, votes in province_votes.items():
            self.city_province[city] = max(votes, key=votes.get)

    def find_by_id(self, national_id: str | None) -> University | None:
        return self.by_key.get(code_key(national_id))

    def find_by_name(self, name: str | None) -> str | None:
        return self.names.get(name)

    def register(self, university: University) -> None:
        self.by_key[code_key(university.national_id)] = university
        self.names.add(university.name, university.national_id)

    def province_for_city(self, city: str | None) -> str:
        return self.city_province.get(norm(city), DEFAULT_PROVINCE) if city else DEFAULT_PROVINCE


def import_universities(db, path: Path, store: UniversityStore, report: Report, **_) -> None:
    df = read_sheet(path)
    table = "دانشگاه‌ها (Addin_Universities)"
    for _, row in df.iterrows():
        report.count(table, "read")
        national_id = digits(row.get("شناسه ملی موسسه"))
        name = clean(row.get("نام موسسه"))
        if not national_id or not name:
            report.count(table, "skipped")
            report.add_todo(table, national_id or "-", name or "-", "شناسه ملی یا نام خالی است")
            continue
        existing = store.find_by_id(national_id)
        if existing is not None:
            report.count(table, "existing")
            if norm(existing.name) != norm(name):
                report.add_diff(table, national_id, "نام", existing.name, name)
            continue
        university = University(
            national_id=national_id,
            tracking_code=clean(row.get("کد رهگیری")),
            name=name,
            city=clean(row.get("شهر")),
            address=clean(row.get("آدرس")),
            province=clean(row.get("استان")) or DEFAULT_PROVINCE,
            university_type=clean(row.get("نوع موسسه")) or _university_type_from_name(name),
            status=clean(row.get("وضعیت")) or DEFAULT_UNIVERSITY_STATUS,
            is_deleted=False,
        )
        db.add(university)
        store.register(university)
        report.count(table, "inserted")
        report.add_new(table, national_id, name)
    db.flush()


# ----------------------------------------------------------- researchers

class ResearcherStore:
    def __init__(self, db) -> None:
        self.by_key: dict[str, Researcher] = {}
        self.names = NameIndex()                       # name -> national_code
        self.by_name_univ: dict[tuple[str, str], str] = {}
        for r in db.query(Researcher).all():
            self.by_key[code_key(r.national_code)] = r
            if not r.is_deleted:
                self._index(r)

    def _index(self, r: Researcher) -> None:
        self.names.add(r.full_name, r.national_code)
        self.by_name_univ[(compact(r.full_name), code_key(r.university_id))] = r.national_code

    def find(self, national_code: str | None) -> Researcher | None:
        return self.by_key.get(code_key(national_code))

    def register(self, r: Researcher) -> None:
        self.by_key[code_key(r.national_code)] = r
        self._index(r)

    def resolve(self, name: str | None, university_id: str | None) -> tuple[str | None, str]:
        """(national_code, how) -- by (name, university) first, then by a
        name that is unique in the whole table."""
        if not name:
            return None, ""
        if university_id:
            hit = self.by_name_univ.get((compact(name), code_key(university_id)))
            if hit:
                return hit, "name+university"
        hit = self.names.get(name)
        return (hit, "name only") if hit else (None, "")


def import_researchers(db, path: Path, universities: UniversityStore,
                       researchers: ResearcherStore, report: Report, **_) -> None:
    df = read_sheet(path)
    table = "فناوران"
    uni_table = "دانشگاه‌ها/موسسات (از ثبت‌نام‌های حقوقی)"

    # Pass 1 -- legal-entity registrations: make sure the entity exists as a
    # University row (the representative is attached to it in pass 2).
    persons: dict[str, dict] = {}
    for _, row in df.iterrows():
        report.count(table, "read")
        reg_type = clean(row.get("نوع ثبت نام")) or ""
        tracking = clean(row.get("کد رهگیری"))
        first = clean(row.get("نام نماینده"))
        last = clean(row.get("نام خانوادگی نماینده"))
        display = f"{first or ''} {last or ''}".strip()
        is_legal = reg_type.startswith(REG_TYPE_LEGAL_PREFIX)

        if is_legal and REG_TYPE_EMPLOYER in reg_type:
            report.count(table, "skipped")
            report.add_todo(table, tracking, display,
                            "ثبت‌نام شرکت مشمول (متقاضی/کارفرما است، فناور نیست) - وارد نشد")
            continue

        entity_id = None
        if is_legal:
            entity_id = digits(row.get("کد ملی / شناسه ملی"))
            person_code = digits(row.get("کد ملی نماینده"))
            entity_name = clean(row.get("دانشگاه / محل خدمت")) or clean(row.get("نام شرکت / موسسه"))
            if not entity_id or not entity_name:
                report.count(table, "unresolved")
                report.add_todo(table, tracking, display, "شخص حقوقی بدون شناسه ملی یا نام موسسه")
                continue
            if universities.find_by_id(entity_id) is None:
                city = clean(row.get("شهر"))
                university = University(
                    national_id=entity_id,
                    tracking_code=tracking,
                    name=entity_name,
                    city=city,
                    address=clean(row.get("آدرس")),
                    province=universities.province_for_city(city),
                    university_type=_university_type_from_name(entity_name),
                    status=DEFAULT_UNIVERSITY_STATUS,
                    is_deleted=False,
                )
                db.add(university)
                universities.register(university)
                report.count(uni_table, "inserted")
                report.add_new(uni_table, entity_id, entity_name,
                               f"استان: {university.province} | نوع: {university.university_type}")
            else:
                report.count(uni_table, "existing")
        else:
            person_code = digits(row.get("کد ملی / شناسه ملی"))

        if not person_code or not first or not last:
            report.count(table, "unresolved")
            report.add_todo(table, tracking, display, "کد ملی/نام خالی یا نامعتبر",
                            row.get("کد ملی / شناسه ملی"))
            continue
        person_code = pad_national_code(person_code)
        if len(person_code) > NATIONAL_CODE_LENGTH:
            report.count(table, "unresolved")
            report.add_todo(table, tracking, display, "کد ملی بیش از ۱۰ رقم", person_code)
            continue

        entry = {
            "row": row, "tracking": tracking, "first": first, "last": last,
            "national_code": person_code, "entity_id": entity_id, "is_legal": is_legal,
            "reg_type": reg_type,
        }
        previous = persons.get(code_key(person_code))
        if previous is not None:
            report.count(table, "skipped")
            # keep the most recent registration; a legal-entity affiliation
            # wins over a plain one (same as the existing data).
            if int(tracking or 0) < int(previous["tracking"] or 0):
                continue
        persons[code_key(person_code)] = entry
    db.flush()

    # Pass 2 -- the researchers themselves.
    for entry in persons.values():
        row = entry["row"]
        code = entry["national_code"]
        full_name = f"{entry['first']} {entry['last']}"

        if entry["is_legal"]:
            university_id = universities.find_by_id(entry["entity_id"]).national_id
        else:
            uni_name = clean(row.get("دانشگاه / محل خدمت"))
            university_id = universities.find_by_name(uni_name)
            if university_id is None:
                report.count(table, "unresolved")
                report.add_todo(
                    table, entry["tracking"], full_name,
                    "دانشگاه/محل خدمت در جدول دانشگاه‌ها پیدا نشد (باید ابتدا اضافه شود)"
                    if uni_name else "دانشگاه/محل خدمت خالی است",
                    uni_name or "",
                )
                continue

        existing = researchers.find(code)
        if existing is not None:
            report.count(table, "existing")
            if code_key(existing.university_id) != code_key(university_id):
                report.add_diff(table, existing.national_code, "دانشگاه/محل خدمت (شناسه)",
                                existing.university_id, university_id)
            if existing.is_deleted:
                report.add_diff(table, existing.national_code, "وضعیت حذف",
                                "حذف‌شده (soft-delete) - بازگردانی نشد", "فعال در ساتع")
            continue

        is_faculty = REG_TYPE_FACULTY in entry["reg_type"]
        researcher = Researcher(
            national_code=code,
            tracking_code=entry["tracking"],
            first_name=entry["first"],
            last_name=entry["last"],
            full_name=full_name,
            mobile=clean(row.get("تلفن همراه")),
            email=clean(row.get("ایمیل")),
            academic_rank=clean(row.get("درجه علمی")) or (None if is_faculty else RESEARCHER_TYPE_TECHNOLOGIST),
            university_id=university_id,
            education_level=clean(row.get("مدرک تحصیلی")),
            researcher_type=RESEARCHER_TYPE_FACULTY if is_faculty else RESEARCHER_TYPE_TECHNOLOGIST,
            status=clean(row.get("وضعیت")) or "Active",
            is_deleted=False,
        )
        db.add(researcher)
        researchers.register(researcher)
        report.count(table, "inserted")
        report.add_new(table, code, full_name, f"دانشگاه: {university_id} | ردیف ساتع: {entry['tracking']}")
    db.flush()


# --------------------------------------------------------------- demands

# Words that differ between SATE's applicant names and the employers table
# ("شرکت نفت فلات قاره ایران" vs "شرکت سهامی نفت فلات قاره"). A match that
# needs them dropped is only used when it is unambiguous, and is flagged in
# the report so it can be eyeballed.
EMPLOYER_FILLER_WORDS = frozenset({
    "شرکت", "سهامی", "عام", "خاص", "ایران", "جمهوری", "اسلامی", "کشور", "سازمان",
})


class EmployerStore:
    def __init__(self, db) -> None:
        self.names = NameIndex(filler_words=EMPLOYER_FILLER_WORDS)
        self.info: dict[str, tuple[str, str]] = {}
        for e in db.query(Employer).filter(Employer.is_deleted == False).all():  # noqa: E712
            self.names.add(e.name, e.classification_code)
            self.info[e.classification_code] = (e.name, e.employer_type)

    def find(self, name: str | None) -> tuple[str | None, bool]:
        """(classification_code, exact_match)."""
        return self.names.get_ex(name)

    def approx_note(self, code: str, file_name: str) -> str:
        return f"تطبیق تقریبی کارفرما: «{file_name}» ← «{self.info[code][0]}» ({code})"


def import_demands(db, path: Path, employers: EmployerStore, report: Report, **_) -> None:
    df = read_sheet(path)
    table = "تقاضاها"
    existing_codes = {c for (c,) in db.query(Demand.tracking_code).all()}
    seen: set[str] = set()
    for _, row in df.iterrows():
        report.count(table, "read")
        code = digits(row.get("کد رهگیری"))
        applicant = clean(row.get("متقاضی"))
        title = clean(row.get("عنوان تقاضا"))
        if not code or not applicant or not title:
            report.count(table, "unresolved")
            report.add_todo(table, code or "-", title or "-", "کد رهگیری/متقاضی/عنوان خالی است")
            continue
        if code in existing_codes:
            report.count(table, "existing")
            continue
        if code in seen:
            report.count(table, "skipped")
            continue
        seen.add(code)

        try:
            demand_date = jalali_to_date(row.get("تاریخ تقاضا"))
        except (TypeError, ValueError):
            demand_date = None
            report.add_todo(table, code, title, "تاریخ تقاضا نامعتبر (رکورد بدون تاریخ وارد شد)",
                            row.get("تاریخ تقاضا"))

        employer_code, exact = employers.find(applicant)
        if employer_code is None:
            report.add_todo(table, code, title,
                            "متقاضی در جدول کارفرمایان پیدا نشد (تقاضا بدون employer_code وارد شد)",
                            applicant)
        elif not exact:
            report.add_todo(table, code, title,
                            "تطبیق تقریبی متقاضی؛ لطفاً درستی را بررسی کنید (وارد شد)",
                            employers.approx_note(employer_code, applicant))

        db.add(Demand(
            tracking_code=code,
            applicant_name=applicant,
            employer_code=employer_code,
            demand_group=clean(row.get("گروه تقاضا")),
            funding_source=clean(row.get("محل تامین اعتبار")),
            demand_nature=clean(row.get("ماهیت تقاضا")),
            demand_domain=clean(row.get("حوزه تقاضا")),
            title=title,
            demand_type=clean(row.get("نوع تقاضا")),
            demand_date=demand_date,
            is_deleted=False,
        ))
        report.count(table, "inserted")
        report.add_new(table, code, title, f"متقاضی: {applicant} -> {employer_code}")
    db.flush()


# ------------------------------------------------------------- proposals

def import_proposals(db, path: Path, universities: UniversityStore,
                     researchers: ResearcherStore, report: Report, **_) -> None:
    df = read_sheet(path)
    table = "پیشنهاده‌ها"

    # status title -> numeric code learned from the data already imported.
    votes: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for title, code in db.query(Proposal.status_title, Proposal.status_code).all():
        if title and code is not None:
            votes[norm(title)][code] += 1
    status_codes = {t: max(v, key=v.get) for t, v in votes.items()}

    demand_titles = NameIndex()
    for code, title in db.query(Demand.tracking_code, Demand.title).filter(Demand.is_deleted == False):  # noqa: E712
        demand_titles.add(title, code)
    # a demand's title is only unique-ish: also index title+applicant
    demand_pairs: dict[tuple[str, str], set] = defaultdict(set)
    for code, title, applicant in db.query(Demand.tracking_code, Demand.title, Demand.applicant_name):
        demand_pairs[(compact(title), compact(applicant))].add(code)

    existing = {p.id: p for p in db.query(Proposal).all()}
    seen: set[int] = set()

    for _, row in df.iterrows():
        report.count(table, "read")
        raw_id = digits(row.get("کد رهگیری"))
        if not raw_id:
            report.count(table, "unresolved")
            report.add_todo(table, "-", clean(row.get("عنوان تقاضا")), "کد رهگیری پیشنهاده نامعتبر")
            continue
        proposal_id = int(raw_id)

        researcher_name = clean(row.get("فناور"))
        university_name = clean(row.get("دانشگاه"))
        status_title = clean(row.get("وضعیت پیشنهاده"))
        status_code = status_codes.get(norm(status_title)) if status_title else None

        university_id = universities.find_by_name(university_name)
        researcher_code, _how = researchers.resolve(researcher_name, university_id)

        demand_title = clean(row.get("عنوان تقاضا"))
        applicant = clean(row.get("متقاضی"))
        pair_hits = demand_pairs.get((compact(demand_title), compact(applicant)), set())
        demand_code = next(iter(pair_hits)) if len(pair_hits) == 1 else demand_titles.get(demand_title)

        current = existing.get(proposal_id)
        if current is not None:
            report.count(table, "existing")
            changed = False
            if status_title and norm(current.status_title) != norm(status_title):
                report.add_diff(table, proposal_id, "وضعیت پیشنهاده", current.status_title,
                                status_title, applied=True)
                current.status_title = status_title
                if status_code is not None:
                    current.status_code = status_code
                changed = True
            for attr, value, label in (
                ("demand_tracking_code", demand_code, "کد تقاضا"),
                ("researcher_code", researcher_code, "کد فناور"),
                ("university_id", university_id, "شناسه دانشگاه"),
            ):
                if getattr(current, attr) is None and value is not None:
                    setattr(current, attr, value)
                    report.add_diff(table, proposal_id, label, None, value, applied=True)
                    changed = True
            if changed:
                report.count(table, "updated")
            continue
        if proposal_id in seen:
            report.count(table, "skipped")
            continue
        seen.add(proposal_id)

        if not researcher_name:
            report.count(table, "unresolved")
            report.add_todo(table, proposal_id, demand_title, "نام فناور خالی است")
            continue
        try:
            submitted_at = jalali_to_date(row.get("تاریخ ارسال پیشنهاده"))
            submitted_at = datetime.combine(submitted_at, datetime.min.time()) if submitted_at else None
        except (TypeError, ValueError):
            submitted_at = None

        db.add(Proposal(
            id=proposal_id,
            demand_tracking_code=demand_code,
            researcher_name=researcher_name,
            researcher_code=researcher_code,
            university_name=university_name,
            university_id=university_id,
            status_code=status_code,
            status_title=status_title,
            submitted_at=submitted_at,
            is_deleted=False,
        ))
        report.count(table, "inserted")
        report.add_new(table, proposal_id, demand_title, f"فناور: {researcher_name}")
        if demand_code is None:
            report.add_todo(table, proposal_id, demand_title,
                            "تقاضای مرتبط پیدا نشد (پیشنهاده بدون demand_tracking_code وارد شد)")
        if researcher_code is None:
            report.add_todo(table, proposal_id, researcher_name,
                            "فناور در جدول فناوران پیدا نشد (پیشنهاده بدون researcher_code وارد شد)")
    db.flush()


# ------------------------------------------------------------- contracts

def import_contracts(db, path: Path, employers: EmployerStore, universities: UniversityStore,
                     researchers: ResearcherStore, report: Report, **_) -> None:
    df = read_sheet(path)
    table = "قراردادها"
    existing = {c.tracking_code: c for c in db.query(Contract).all()}
    seen: set[str] = set()

    for _, row in df.iterrows():
        report.count(table, "read")
        code = digits(row.get("کد رهگیری"))
        title = clean(row.get("عنوان قرارداد"))
        if not code or not title:
            report.count(table, "unresolved")
            report.add_todo(table, code or "-", title or "-", "کد رهگیری یا عنوان خالی است")
            continue

        try:
            amount = int(float(clean(row.get("مبلغ قرارداد(ریال)")) or ""))
        except ValueError:
            report.count(table, "unresolved")
            report.add_todo(table, code, title, "مبلغ قرارداد خالی/نامعتبر", row.get("مبلغ قرارداد(ریال)"))
            continue
        try:
            contract_date = jalali_to_date(row.get("تاریخ قرارداد"))
        except (TypeError, ValueError):
            report.count(table, "unresolved")
            report.add_todo(table, code, title, "تاریخ قرارداد نامعتبر", row.get("تاریخ قرارداد"))
            continue
        proposal_id = digits(row.get("شناسه پیشنهاده"))

        current = existing.get(code)
        if current is not None:
            report.count(table, "existing")
            if int(current.total_amount) != amount:
                report.add_diff(table, code, "مبلغ قرارداد (ریال)", int(current.total_amount), amount)
            if current.contract_date != contract_date:
                report.add_diff(table, code, "تاریخ قرارداد", current.contract_date, contract_date)
            if proposal_id and (current.proposal_id or "") not in (proposal_id, code):
                report.add_diff(table, code, "شناسه پیشنهاده", current.proposal_id, proposal_id)
            if compact(current.title) != compact(title):
                report.add_diff(table, code, "عنوان", current.title, title)
            if current.is_deleted:
                report.add_diff(table, code, "وضعیت حذف", "حذف‌شده (soft-delete) - بازگردانی نشد",
                                "موجود در ساتع")
            continue
        if code in seen:
            report.count(table, "skipped")
            continue
        seen.add(code)

        employer_name = clean(row.get("متقاضی"))
        employer_code, employer_exact = employers.find(employer_name)
        if employer_code is None:
            report.count(table, "unresolved")
            report.add_todo(table, code, title,
                            "کارفرما در جدول کارفرمایان پیدا نشد (ابتدا کارفرما اضافه شود)", employer_name)
            continue
        employer_type = employers.info[employer_code][1]
        if employer_type not in ALLOWED_CONTRACT_EMPLOYER_TYPES:
            report.count(table, "unresolved")
            report.add_todo(table, code, title,
                            f"کارفرما از نوع «{employer_type}» است و نمی‌تواند قرارداد داشته باشد",
                            employer_name)
            continue

        university_name = clean(row.get("دانشگاه"))
        university_id = universities.find_by_name(university_name)
        if university_id is None:
            report.count(table, "unresolved")
            report.add_todo(table, code, title,
                            "دانشگاه/موسسه در جدول دانشگاه‌ها پیدا نشد (ابتدا اضافه شود)", university_name)
            continue

        researcher_name = clean(row.get("فناور"))
        researcher_id, how = researchers.resolve(researcher_name, university_id)
        if researcher_id is None:
            report.count(table, "unresolved")
            report.add_todo(table, code, title,
                            "فناور در جدول فناوران پیدا نشد (ابتدا فناور اضافه شود)", researcher_name)
            continue

        try:
            duration = int(float(clean(row.get("مدت زمان اجرا (ماه)")) or ""))
        except ValueError:
            duration = None

        db.add(Contract(
            tracking_code=code,
            employer_code=employer_code,
            university_id=university_id,
            researcher_id=researcher_id,
            proposal_id=proposal_id,
            contract_number=clean(row.get("شماره قرارداد")),
            contract_date=contract_date,
            total_amount=amount,
            title=title,
            duration_months=duration,
            status=clean(row.get("وضعیت")) or "Active",
            is_deleted=False,
        ))
        report.count(table, "inserted")
        note = f"کارفرما: {employer_code} | فناور: {researcher_name}"
        if not employer_exact:
            note += " | " + employers.approx_note(employer_code, employer_name)
        if how == "name only":
            note += " | (فناور فقط با نام یکتا پیدا شد؛ دانشگاه فناور در پایگاه متفاوت است)"
        report.add_new(table, code, title, note)
    db.flush()


# ------------------------------------------------------------------ main

def main() -> int:
    parser = argparse.ArgumentParser(description="Import SATE exports from data/Add_In")
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR, help="folder holding the Addin_*.xlsx files")
    parser.add_argument("--dry-run", action="store_true", help="match and report only; write nothing")
    parser.add_argument("--only", default="", help="comma separated subset of: " + ",".join(STEP_ORDER))
    args = parser.parse_args()

    selected = [s for s in STEP_ORDER if not args.only or s in {x.strip() for x in args.only.split(",")}]
    files = {step: args.dir / FILE_NAMES[step] for step in selected}
    present = [s for s in selected if files[s].exists()]
    for step in selected:
        print(f"{'[OK]  ' if step in present else '[--]  '}{FILE_NAMES[step]}"
              f"{'' if step in present else '  (یافت نشد - رد می‌شود)'}")
    if not present:
        print("هیچ فایلی برای ایمپورت پیدا نشد.")
        return 1

    db = SessionLocal()
    report = Report()
    try:
        db.autoflush = False
        universities = UniversityStore(db)
        researchers = ResearcherStore(db)
        employers = EmployerStore(db)
        ctx = dict(db=db, universities=universities, researchers=researchers,
                   employers=employers, report=report)
        runners = {
            "universities": import_universities,
            "researchers": import_researchers,
            "demands": import_demands,
            "proposals": import_proposals,
            "contracts": import_contracts,
        }
        for step in present:
            print(f"\n--- {FILE_NAMES[step]} ---")
            runners[step](path=files[step], **ctx)

        if args.dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("\n" + "=" * 70)
    print("خلاصه" + (" (dry-run: چیزی نوشته نشد)" if args.dry_run else ""))
    print("=" * 70)
    for row in report.summary_rows():
        print(" | ".join(f"{k}: {v}" for k, v in row.items()))
    print(f"موارد نیازمند اقدام: {len(report.todo)}  |  تفاوت با پایگاه داده: {len(report.diff)}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report.save(REPORT_DIR / f"addin_import_{stamp}{'_dryrun' if args.dry_run else ''}.xlsx", args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
