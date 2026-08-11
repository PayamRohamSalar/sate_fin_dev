# Directory Structure
./
    create_project_structure.py
    generate_context.py
    main.py
    SATE_codebase_context.md
    test_engine_cli.py
    .cursor/
    .pgdata/
        base/
            1/
            16384/
            4/
            5/
        global/
        pg_commit_ts/
        pg_dynshmem/
        pg_logical/
            mappings/
            snapshots/
        pg_multixact/
            members/
            offsets/
        pg_notify/
        pg_replslot/
        pg_serial/
        pg_snapshots/
        pg_stat/
        pg_stat_tmp/
        pg_subtrans/
        pg_tblspc/
        pg_twophase/
        pg_wal/
            archive_status/
            summaries/
        pg_xact/
    api/
        __init__.py
        v1/
            api_router.py
            __init__.py
            endpoints/
                contracts.py
                employers.py
                payments.py
                researchers.py
                universities.py
                __init__.py
    core/
        database.py
        date_helper.py
    dashboard/
        app.py
        app_v2.py
        CHANGELOG.md
        QUICKSTART.md
        README.md
        views/
            batch_payments_page.py
            contract_edit_page.py
            contract_entry_page.py
            researcher_entry_page.py
            university_entry_page.py
    data/
        Archive/
            Contracts/
            Payments/
    Docs/
        Phase1_Complete.md
        Phase2_Start.md
        Phase3_Dashboard_Complete.md
        SATE_Living_Documentation.md
        Technical Transition Report_R2.md
    models/
        contract.py
        deposits.py
        employer.py
        payment.py
        researchers.py
        transfer.py
        university.py
    results/
    schemas/
        contract_schema.py
        employer_schema.py
        payment_schema.py
        researcher_schema.py
        university_schema.py
        __init__.py
    scripts/
        add_contract_attachment_path.py
        add_payment_missing_columns.py
        add_payment_status_column.py
        append_new_mandates.py
        chart01_total_trend.py
        check_excel.py
        create_transfer_table.py
        example_1.py
        fix_university_names.py
        generate_contract_status_report.py
        generate_financial_report.py
        import_contracts.py
        import_contracts_upsert.py
        import_credit_transfers.py
        import_credit_transfers_addin.py
        import_deposits.py
        import_employers.py
        import_payments.py
        import_payments_upsert.py
        import_researchers.py
        import_researchers_upsert.py
        import_universities.py
        import_universities_upsert.py
        process_budgets.py
        verify_universities.py
    services/
        financial_engine.py


# File Contents
==================================================

## File: create_project_structure.py
------------------------------
from pathlib import Path

# مسیر اصلی پروژه
project_path = Path(r"D:\OneDrive\AI-Project\SATE_Fin_Dev")

# پوشه‌هایی که باید ساخته شوند
folders = [
    "core",
    "models",
    "data",
    "scripts",
]

# ساخت مسیر اصلی پروژه در صورت نبودن
project_path.mkdir(parents=True, exist_ok=True)

# ساخت پوشه‌ها
for folder in folders:
    folder_path = project_path / folder
    folder_path.mkdir(exist_ok=True)

# ساخت فایل .env در صورت نبودن
env_file = project_path / ".env"

if not env_file.exists():
    env_file.write_text(
        """# Environment Variables
# Database Configuration

DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
""",
        encoding="utf-8"
    )

print("ساختار پروژه با موفقیت ایجاد شد:")
print(project_path)


## File: generate_context.py
------------------------------
import os

def generate_codebase_summary(root_dir, output_file):
    """
    Traverses the project directory, creates a tree structure,
    and appends the content of relevant files.
    """
    # Exclude directories that do not contain source code
    ignore_dirs = {'.git', '__pycache__', 'venv', 'env', '.idea', '.vscode'}
    
    # Target specific file types relevant to SATE Financial System MVP
    allowed_extensions = {'.py', '.sql', '.md', '.json', '.env.example'}

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 1. Document the Directory Structure
        outfile.write("# Directory Structure\n")
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            level = root.replace(root_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            outfile.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                if any(f.endswith(ext) for ext in allowed_extensions):
                    outfile.write(f"{sub_indent}{f}\n")

        outfile.write("\n\n# File Contents\n")
        outfile.write("="*50 + "\n\n")

        # 2. Append the Content of Each Target File
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in files:
                if any(f.endswith(ext) for ext in allowed_extensions):
                    file_path = os.path.join(root, f)
                    relative_path = os.path.relpath(file_path, root_dir)
                    
                    outfile.write(f"## File: {relative_path}\n")
                    outfile.write("-" * 30 + "\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read() + "\n\n")
                    except Exception as e:
                        outfile.write(f"[Error reading file: {e}]\n\n")

if __name__ == "__main__":
    # Run in the current SATE_Fin_Dev directory
    project_path = "." 
    output_filename = "SATE_codebase_context.md"
    generate_codebase_summary(project_path, output_filename)
    print(f"Success! Please upload '{output_filename}' to the chat.")

## File: main.py
------------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.api_router import api_router

app = FastAPI(
    title="SATE Financial System API",
    description="Backend REST API for SATE Financial Dashboard (MVP)",
    version="1.0.0"
)

# CORS configuration for Frontend (Streamlit/React) integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
def health_check():
    """
    Root endpoint to verify the API is running.
    """
    return {
        "status": "Operational", 
        "message": "Welcome to SATE Financial System API",
        "phase": 2
    }


## File: SATE_codebase_context.md
------------------------------


## File: test_engine_cli.py
------------------------------
#!/usr/bin/env python3
"""
CLI Test Script for Financial Engine
=====================================
This script directly tests the calculate_real_balance function from the financial engine
by fetching a real employer from the database and calculating their balance.
"""

from sqlalchemy.orm import Session
from core.database import SessionLocal
from services.financial_engine import calculate_real_balance
from models.employer import Employer


def test_financial_engine():
    """
    Test the financial engine by calculating balance for a real employer from the database.
    """
    print("=" * 70)
    print("SATE Financial Engine - CLI Test")
    print("=" * 70)
    
    # Initialize database session
    db: Session = SessionLocal()
    
    try:
        # Fetch one employer from the database dynamically
        employer = db.query(Employer).filter(
            Employer.is_deleted == False
        ).first()
        
        if not employer:
            print("\n❌ No employers found in the database.")
            print("Please ensure the database is populated with employer data.")
            return
        
        print(f"\n✓ Found Employer: {employer.name}")
        print(f"  Classification Code: {employer.classification_code}")
        print(f"  Parent Code: {employer.parent_code or 'N/A (Top-level employer)'}")
        
        # Test for multiple funding years
        test_years = [1402, 1403, 1404]
        
        print(f"\n{'Year':<10} {'Balance (Rials)':<20} {'Status':<15}")
        print("-" * 70)
        
        for year in test_years:
            try:
                balance = calculate_real_balance(
                    db=db,
                    employer_code=employer.classification_code,
                    funding_year=year
                )
                
                # Format the balance with thousand separators
                balance_formatted = f"{balance:,.2f}"
                status = "✓ Success"
                
                print(f"{year:<10} {balance_formatted:<20} {status:<15}")
                
            except Exception as e:
                print(f"{year:<10} {'Error':<20} ❌ {str(e)}")
        
        print("\n" + "=" * 70)
        print("Test completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
        print("\n✓ Database connection closed.")


if __name__ == "__main__":
    test_financial_engine()


## File: api\__init__.py
------------------------------


## File: api\v1\api_router.py
------------------------------
from fastapi import APIRouter

from api.v1.endpoints import contracts, employers, payments, universities, researchers

# Create the main API router for version 1
api_router = APIRouter()

# Include sub-routers for different endpoint groups
api_router.include_router(employers.router)
api_router.include_router(payments.router)
api_router.include_router(contracts.router)
api_router.include_router(universities.router)
api_router.include_router(researchers.router)

# Future routers can be added here as the system grows:
# api_router.include_router(deposits.router)


## File: api\v1\__init__.py
------------------------------


## File: api\v1\endpoints\contracts.py
------------------------------
import logging
import traceback
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.exc import (
    DataError,
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session

from core.database import get_db
from models.contract import Contract
from models.employer import Employer
from models.researchers import Researcher
from models.university import University
from schemas.contract_schema import (
    ContractCreate,
    ContractDetail,
    ContractSearchResult,
    ContractUpdate,
)

router = APIRouter(prefix="/contracts", tags=["Contracts"])
logger = logging.getLogger(__name__)

DUPLICATE_CONTRACT_MESSAGE = "کد رهگیری تکراری است."
CONTRACT_DATA_MISMATCH_MESSAGE = (
    "خطای یکپارچگی اطلاعات: کارفرما، دانشگاه یا فناور نامعتبر است."
)
CONTRACT_DATA_FORMAT_MESSAGE = (
    "نوع یا طول داده‌های ارسالی نامعتبر است (مثلا فرمت تاریخ یا مبالغ)."
)
CONTRACT_CONNECTION_ERROR_MESSAGE = (
    "خطا در ارتباط با پایگاه داده. لطفاً چند لحظه دیگر دوباره تلاش کنید."
)
ALLOWED_CONTRACT_EMPLOYER_TYPES = {"Mother", "Independent"}


def _optional_text(value: str | None) -> str | None:
    """Normalize optional text values before database persistence."""
    if value is None:
        return None
    normalized_value = value.strip()
    return normalized_value or None


def _is_unique_violation(error: IntegrityError) -> bool:
    """Return whether an integrity error represents a unique-key conflict."""
    original_error = error.orig
    sqlstate = getattr(original_error, "sqlstate", None) or getattr(
        original_error, "pgcode", None
    )
    if sqlstate == "23505":
        return True

    return "unique constraint" in str(original_error).lower()


def _is_foreign_key_violation(error: IntegrityError) -> bool:
    """Return whether an integrity error represents a foreign-key conflict."""
    original_error = error.orig
    sqlstate = getattr(original_error, "sqlstate", None) or getattr(
        original_error, "pgcode", None
    )
    if sqlstate == "23503":
        return True

    return "foreign key" in str(original_error).lower()


def _raise_contract_persistence_error(
    error: SQLAlchemyError,
    tracking_code: str,
) -> None:
    """Map a failed contract write to a localized API error."""
    logger.exception("Failed to persist contract '%s': %s", tracking_code, error)

    if isinstance(error, IntegrityError) and _is_unique_violation(error):
        raise HTTPException(
            status_code=409,
            detail=DUPLICATE_CONTRACT_MESSAGE.format(tracking_code=tracking_code),
        ) from error

    if isinstance(error, IntegrityError) and _is_foreign_key_violation(error):
        raise HTTPException(
            status_code=400,
            detail=CONTRACT_DATA_MISMATCH_MESSAGE,
        ) from error

    if isinstance(error, DataError):
        raise HTTPException(
            status_code=400,
            detail=CONTRACT_DATA_FORMAT_MESSAGE,
        ) from error

    raise HTTPException(
        status_code=400,
        detail=CONTRACT_DATA_MISMATCH_MESSAGE,
    ) from error


def _raise_contract_connection_error(
    error: Exception,
    tracking_code: str,
) -> None:
    """Log a database connectivity failure and return a retryable 503 error.

    Handles both SQLAlchemy's wrapped ``OperationalError`` and a raw
    ``ConnectionResetError`` that may surface if the connection drops before
    the driver wraps it, so a mid-request network failure never escapes as an
    unhandled exception.
    """
    logger.error(
        "Database connection failure while persisting contract '%s': %s",
        tracking_code,
        error,
    )
    raise HTTPException(
        status_code=503,
        detail=CONTRACT_CONNECTION_ERROR_MESSAGE,
    ) from error


def _raise_unexpected_contract_error(
    error: Exception,
    tracking_code: str,
) -> None:
    """Log an unexpected contract failure and return a safe server error."""
    logger.error(
        "Unexpected contract persistence error for '%s': %s",
        tracking_code,
        error,
    )
    print(traceback.format_exc())
    raise HTTPException(
        status_code=500,
        detail="خطا در ذخیره قرارداد. لطفاً مجدداً تلاش کنید.",
    ) from error


def _get_active_contract_parties(
    db: Session,
    payload: ContractCreate | ContractUpdate,
) -> tuple[Employer, University, Researcher]:
    """Load active contract parties and enforce employer business rules.

    Shared by both contract creation and contract update, since
    ``ContractCreate`` and ``ContractUpdate`` expose identical
    employer/university/researcher fields.
    """
    employer = (
        db.query(Employer)
        .filter(
            Employer.classification_code
            == payload.employer_classification_code,
            Employer.is_deleted == False,
        )
        .first()
    )
    if employer is None:
        raise HTTPException(
            status_code=404,
            detail="کارفرمای انتخاب‌شده یافت نشد یا حذف شده است.",
        )
    if employer.employer_type not in ALLOWED_CONTRACT_EMPLOYER_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "خطا: قرارداد فقط باید به نام شرکت مادر یا مستقل ثبت شود."
            ),
        )

    university = (
        db.query(University)
        .filter(
            University.national_id == payload.university_national_id,
            University.is_deleted == False,
        )
        .first()
    )
    if university is None:
        raise HTTPException(
            status_code=404,
            detail="دانشگاه انتخاب‌شده یافت نشد یا حذف شده است.",
        )

    researcher = (
        db.query(Researcher)
        .filter(
            Researcher.national_code == payload.researcher_national_id,
            Researcher.is_deleted == False,
        )
        .first()
    )
    if researcher is None:
        raise HTTPException(
            status_code=404,
            detail="فناور انتخاب‌شده یافت نشد یا حذف شده است.",
        )

    return employer, university, researcher


def _to_search_result(
    contract: Contract,
    employer: Employer,
    university: University,
    researcher: Researcher,
) -> ContractSearchResult:
    """Build the public contract response from persisted entities."""
    return ContractSearchResult(
        contract_tracking_code=contract.tracking_code,
        title=contract.title,
        employer_name=employer.name,
        employer_classification_code=employer.classification_code,
        university_name=university.name,
        researcher_name=researcher.full_name,
    )


@router.get("/search", response_model=List[ContractSearchResult])
def search_contracts(
    q: str = Query(
        ...,
        min_length=1,
        description="Search term matched against tracking code or title",
    ),
    db: Session = Depends(get_db),
):
    """Search active contracts and active related entities for auto-fill."""
    like_pattern = f"%{q}%"
    rows = (
        db.query(
            Contract.tracking_code.label("contract_tracking_code"),
            Contract.title.label("title"),
            Employer.name.label("employer_name"),
            Employer.classification_code.label(
                "employer_classification_code"
            ),
            University.name.label("university_name"),
            Researcher.full_name.label("researcher_name"),
        )
        .join(
            Employer,
            and_(
                Contract.employer_code == Employer.classification_code,
                Employer.is_deleted == False,
            ),
        )
        .join(
            University,
            and_(
                Contract.university_id == University.national_id,
                University.is_deleted == False,
            ),
        )
        .join(
            Researcher,
            and_(
                Contract.researcher_id == Researcher.national_code,
                Researcher.is_deleted == False,
            ),
        )
        .filter(
            Contract.is_deleted == False,
            or_(
                Contract.tracking_code.ilike(like_pattern),
                Contract.title.ilike(like_pattern),
            ),
        )
        .all()
    )

    return [ContractSearchResult(**row._asdict()) for row in rows]


@router.post("/", response_model=ContractSearchResult, status_code=201)
def create_contract(
    payload: ContractCreate,
    db: Session = Depends(get_db),
):
    """Register a contract, keeping the full lookup-and-write flow inside one
    transaction-safe try/except so any failure — validation, persistence, or
    a dropped database connection — rolls back cleanly and returns a proper
    HTTP error instead of an unhandled exception.
    """
    tracking_code = payload.tracking_code.strip()
    title = payload.title.strip()
    if not tracking_code or not title:
        raise HTTPException(
            status_code=400,
            detail="کد رهگیری و عنوان قرارداد الزامی هستند.",
        )

    try:
        existing_contract = (
            db.query(Contract.tracking_code)
            .filter(
                Contract.tracking_code == tracking_code,
                Contract.is_deleted == False,
            )
            .first()
        )
        if existing_contract is not None:
            raise HTTPException(
                status_code=409,
                detail=DUPLICATE_CONTRACT_MESSAGE.format(
                    tracking_code=tracking_code
                ),
            )

        employer, university, researcher = _get_active_contract_parties(
            db, payload
        )
        contract_date: date = payload.contract_date
        contract = Contract(
            tracking_code=tracking_code,
            employer_code=payload.employer_classification_code,
            university_id=payload.university_national_id,
            researcher_id=payload.researcher_national_id,
            contract_number=_optional_text(payload.contract_number),
            proposal_id=_optional_text(payload.proposal_id),
            attachment_path=_optional_text(payload.attachment_path),
            title=title,
            total_amount=payload.total_amount,
            contract_date=contract_date,
            duration_months=payload.duration_months,
            status="فعال",
            is_deleted=False,
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        _raise_contract_persistence_error(exc, tracking_code)
    except DataError as exc:
        db.rollback()
        _raise_contract_persistence_error(exc, tracking_code)
    except (OperationalError, ConnectionResetError) as exc:
        db.rollback()
        _raise_contract_connection_error(exc, tracking_code)
    except SQLAlchemyError as exc:
        db.rollback()
        _raise_unexpected_contract_error(exc, tracking_code)
    except Exception as exc:
        db.rollback()
        _raise_unexpected_contract_error(exc, tracking_code)

    return _to_search_result(contract, employer, university, researcher)


CONTRACT_NOT_FOUND_MESSAGE = "قرارداد یافت نشد یا حذف شده است."


def _get_active_contract_or_404(db: Session, tracking_code: str) -> Contract:
    """Fetch a non-soft-deleted contract by tracking code or raise a 404."""
    contract = (
        db.query(Contract)
        .filter(
            Contract.tracking_code == tracking_code,
            Contract.is_deleted == False,
        )
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail=CONTRACT_NOT_FOUND_MESSAGE)
    return contract


def _to_detail(contract: Contract) -> ContractDetail:
    """Build the full-detail response used to populate the edit form."""
    return ContractDetail(
        tracking_code=contract.tracking_code,
        employer_classification_code=contract.employer_code,
        university_national_id=contract.university_id,
        researcher_national_id=contract.researcher_id,
        contract_number=contract.contract_number,
        proposal_id=contract.proposal_id,
        attachment_path=contract.attachment_path,
        title=contract.title,
        total_amount=int(contract.total_amount),
        contract_date=contract.contract_date,
        duration_months=contract.duration_months,
        status=contract.status,
    )


@router.get("/{tracking_code}", response_model=ContractDetail)
def get_contract(
    tracking_code: str,
    db: Session = Depends(get_db),
):
    """Fetch the full details of a single active contract for editing."""
    contract = _get_active_contract_or_404(db, tracking_code)
    return _to_detail(contract)


@router.put("/{tracking_code}", response_model=ContractSearchResult)
def update_contract(
    tracking_code: str,
    payload: ContractUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing active contract's editable fields.

    Reuses the same party-resolution/business-rule check, optional-text
    normalization, and layered error handling as :func:`create_contract` so
    an update is validated exactly as strictly as a fresh registration.
    """
    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=400,
            detail="عنوان قرارداد الزامی است.",
        )

    try:
        contract = _get_active_contract_or_404(db, tracking_code)
        employer, university, researcher = _get_active_contract_parties(
            db, payload
        )

        contract.employer_code = payload.employer_classification_code
        contract.university_id = payload.university_national_id
        contract.researcher_id = payload.researcher_national_id
        contract.contract_number = _optional_text(payload.contract_number)
        contract.proposal_id = _optional_text(payload.proposal_id)
        contract.attachment_path = _optional_text(payload.attachment_path)
        contract.title = title
        contract.total_amount = payload.total_amount
        contract.contract_date = payload.contract_date
        contract.duration_months = payload.duration_months

        db.commit()
        db.refresh(contract)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        _raise_contract_persistence_error(exc, tracking_code)
    except DataError as exc:
        db.rollback()
        _raise_contract_persistence_error(exc, tracking_code)
    except (OperationalError, ConnectionResetError) as exc:
        db.rollback()
        _raise_contract_connection_error(exc, tracking_code)
    except SQLAlchemyError as exc:
        db.rollback()
        _raise_unexpected_contract_error(exc, tracking_code)
    except Exception as exc:
        db.rollback()
        _raise_unexpected_contract_error(exc, tracking_code)

    return _to_search_result(contract, employer, university, researcher)


## File: api\v1\endpoints\employers.py
------------------------------
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from core.database import get_db
from services.financial_engine import calculate_real_balance
from schemas.employer_schema import BalanceResponse
from models.employer import Employer

router = APIRouter(
    prefix="/employers",
    tags=["Employers"]
)


@router.get("/{employer_id}/balance", response_model=BalanceResponse)
def get_employer_balance(
    employer_id: str = Path(..., description="Employer classification code"),
    funding_year: int = Query(..., description="Funding year (fiscal year) for balance calculation", ge=1300, le=1500),
    db: Session = Depends(get_db)
):
    """
    Calculate and return the real financial balance for a specific employer and funding year.

    The balance is calculated as:
    (Total Deposits + Transfers In) - (Total Payments + Transfers Out)

    Deposits include subsidiary receipts for Mother employers.
    
    **Parameters:**
    - `employer_id`: The employer's classification code
    - `funding_year`: The fiscal year for the balance calculation (Persian calendar year)
    
    **Returns:**
    - Employer code
    - Funding year
    - Total calculated balance
    - Current inquiry date in Jalali format
    """
    
    # Verify that the employer exists in the database
    employer = db.query(Employer).filter(
        Employer.classification_code == employer_id,
        Employer.is_deleted == False
    ).first()
    
    if not employer:
        raise HTTPException(
            status_code=404,
            detail=f"Employer with code '{employer_id}' not found or has been deleted."
        )
    
    # Calculate the real balance using the financial engine
    try:
        balance = calculate_real_balance(db, employer_id, funding_year)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating balance: {str(e)}"
        )
    
    # Return the response with current Jalali date
    return BalanceResponse(
        employer_code=employer_id,
        funding_year=funding_year,
        total_balance=balance,
        inquiry_date_jalali=BalanceResponse.get_current_jalali_date()
    )

@router.get("/lookup", summary="Employer lookup for dropdowns")
def employer_lookup(db: Session = Depends(get_db)):
    """Return classification_code + name for non-subsidiary employers."""
    rows = db.query(Employer.classification_code, Employer.name).filter(
        Employer.employer_type != "Subsidiary",
        Employer.is_deleted == False,
    ).order_by(Employer.name).all()
    return [{"classification_code": code, "name": name} for code, name in rows]


## File: api\v1\endpoints\payments.py
------------------------------
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query as SAQuery
from sqlalchemy.orm import Session

from core.database import get_db
from models.contract import Contract
from models.employer import Employer
from models.payment import Payment
from models.university import University
from schemas.payment_schema import (
    DraftDeleteResponse,
    FinalizeBatchRequest,
    FinalizeBatchResponse,
    PaymentDraftCreate,
    PaymentDraftCreateResponse,
    PaymentDraftResponse,
    PaymentValidationRequest,
    PaymentValidationResponse,
)
from services.financial_engine import (
    InsufficientFundsError,
    calculate_real_balance,
    validate_payment_impact,
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post("/validate", response_model=PaymentValidationResponse)
def validate_payment(
    request: PaymentValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate the impact of a payment on the employer's balance without registering it.

    **Business Rule (updated):** negative balances are a hard block, not a
    warning — a payment that would take the employer's balance below zero
    returns HTTP 400, not HTTP 200 with a warning message. This mirrors the
    same check ``POST /payments/draft`` performs before staging a draft.

    **Parameters:**
    - `contract_tracking_code`: The contract tracking code
    - `amount`: The payment amount to validate
    - `funding_year`: The funding year for the payment

    **Returns:**
    - Current balance and projected balance for an affordable payment.
    """
    try:
        validation_result = validate_payment_impact(
            db=db,
            contract_code=request.contract_tracking_code,
            payment_amount=request.amount,
            funding_year=request.funding_year,
            lock_rows=True,
        )
        db.rollback()  # Read-only check: release the row locks immediately.
    except InsufficientFundsError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error validating payment: {str(exc)}"
        )

    return PaymentValidationResponse(
        employer_code=validation_result["employer_code"],
        current_balance=validation_result["current_balance"],
        payment_amount=validation_result["payment_amount"],
        new_balance=validation_result["new_balance"],
        is_negative=False,
        warning_message=None,
    )


def _enriched_payment_query(db: Session) -> SAQuery:
    """Build the shared Payment+Contract+Employer+University join.

    Every join is on a single FK to a single PK (Payment -> Contract is
    many-to-one, Contract -> Employer/University are each many-to-one), so
    this always returns exactly one row per ``Payment`` — no fan-out, no
    Cartesian product, and no N+1 (a single query regardless of row count).
    ``outerjoin`` is used throughout so a payment is still returned even if
    its contract or a downstream link is missing/soft-deleted-adjacent.
    """
    return (
        db.query(Payment, Contract, Employer, University)
        .outerjoin(
            Contract, Payment.contract_tracking_code == Contract.tracking_code
        )
        .outerjoin(
            Employer, Contract.employer_code == Employer.classification_code
        )
        .outerjoin(
            University, Contract.university_id == University.national_id
        )
    )


def _compute_balances_after(
    db: Session,
    rows: list[tuple[Payment, Contract, Employer, University]],
) -> dict[str, float]:
    """Compute each payment's employer balance immediately after it.

    ``calculate_real_balance`` already sums every ``Draft``/``Final``
    payment for an (employer, funding_year) pair, so it reflects the state
    *after all* of ``rows`` are applied. To show a distinct, meaningful
    "balance after this row" per row (not just the same final number
    repeated), payments are grouped by (employer_code, funding_year), the
    group's amounts are added back to get the balance *before* any of them,
    and a running balance is walked forward in tracking-code order.

    Only one ``calculate_real_balance`` call is made per distinct
    (employer_code, funding_year) pair present in ``rows`` — not one per
    row — regardless of how many payments share that pair.

    Returns:
        A ``{tracking_code: balance_after}`` map.
    """
    groups: dict[tuple[str, int], list[Payment]] = {}
    for payment, _contract, employer, _university in rows:
        if employer is None:
            continue
        key = (employer.classification_code, payment.funding_year)
        groups.setdefault(key, []).append(payment)

    balance_after: dict[str, float] = {}
    for (employer_code, funding_year), group_payments in groups.items():
        current_balance = calculate_real_balance(db, employer_code, funding_year)
        # current_balance already includes every payment in this group;
        # add them all back to recover the balance before any of them.
        running_balance = current_balance + sum(
            float(p.amount) for p in group_payments
        )
        for payment in sorted(group_payments, key=lambda p: p.tracking_code):
            running_balance -= float(payment.amount)
            balance_after[payment.tracking_code] = running_balance

    return balance_after


def _to_draft_response(
    payment: Payment,
    contract: Contract,
    employer: Employer,
    university: University,
    *,
    balance_after: float | None = None,
) -> PaymentDraftResponse:
    """Build the display-ready draft response from the joined entities."""
    return PaymentDraftResponse(
        tracking_code=payment.tracking_code,
        contract_tracking_code=payment.contract_tracking_code,
        contract_title=contract.title if contract else None,
        contract_total_amount=float(contract.total_amount) if contract else None,
        employer_code=employer.classification_code if employer else None,
        employer_name=employer.name if employer else None,
        university_name=university.name if university else None,
        amount=float(payment.amount),
        funding_year=payment.funding_year,
        payment_year=payment.payment_year,
        series=payment.series,
        status=payment.status,
        employer_balance_after=balance_after,
    )


@router.post("/draft", response_model=PaymentDraftCreateResponse, status_code=201)
def create_draft_payment(
    request: PaymentDraftCreate,
    db: Session = Depends(get_db),
):
    """
    Stage a single payment as a database-backed draft (batch-payment cart).

    Replaces the old in-memory ``st.session_state`` cart: drafts are
    persisted immediately, so they survive a browser reload, and their
    amount is reserved against the employer's real balance the instant
    they are created (``calculate_real_balance`` counts ``Draft`` rows
    alongside ``Final`` ones). A payment that would drive the balance
    negative is rejected outright with HTTP 400 — there is no warning-only
    path anymore.

    **Parameters:**
    - `tracking_code`: Unique payment tracking code (primary key).
    - `contract_tracking_code`: Contract the payment is drawn against.
    - `amount`: Payment amount in base Rials.
    - `funding_year`: Fiscal year the balance check and reservation apply to.
    - `payment_year`, `series`, `notification_letter_number`,
      `notification_date`: Optional metadata.

    **Returns:**
    - The created draft, HTTP 201, including `employer_balance_before` and
      `employer_balance_after` so the frontend can show the balance
      transition without a second API call.

    **Raises:**
    - `HTTPException(400)`: Duplicate tracking code, or insufficient funds.
    - `HTTPException(404)`: The contract or its employer is missing/deleted.
    """
    existing = (
        db.query(Payment.tracking_code)
        .filter(
            Payment.tracking_code == request.tracking_code,
            Payment.is_deleted == False,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"خطا: کد رهگیری پرداخت '{request.tracking_code}' "
                "قبلاً در سیستم ثبت شده است."
            ),
        )

    try:
        validation_result = validate_payment_impact(
            db=db,
            contract_code=request.contract_tracking_code,
            payment_amount=request.amount,
            funding_year=request.funding_year,
            lock_rows=True,
        )
    except InsufficientFundsError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc))

    try:
        payment = Payment(
            tracking_code=request.tracking_code,
            contract_tracking_code=request.contract_tracking_code,
            amount=request.amount,
            funding_year=request.funding_year,
            payment_year=request.payment_year,
            series=request.series,
            notification_letter_number=request.notification_letter_number,
            notification_date=request.notification_date,
            status="Draft",
            is_deleted=False,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=(
                f"خطا: کد رهگیری پرداخت '{request.tracking_code}' "
                "قبلاً در سیستم ثبت شده است."
            ),
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"خطا در ذخیره پیش‌نویس پرداخت: {exc}",
        )

    # Single joined round-trip for the display-ready contract/employer/
    # university fields, rather than one query per related entity.
    contract, employer, university = (
        db.query(Contract, Employer, University)
        .outerjoin(
            Employer, Contract.employer_code == Employer.classification_code
        )
        .outerjoin(
            University, Contract.university_id == University.national_id
        )
        .filter(Contract.tracking_code == payment.contract_tracking_code)
        .first()
    )

    base_response = _to_draft_response(
        payment,
        contract,
        employer,
        university,
        balance_after=validation_result["new_balance"],
    )
    return PaymentDraftCreateResponse(
        **base_response.model_dump(),
        employer_balance_before=validation_result["current_balance"],
    )


@router.get("/drafts", response_model=List[PaymentDraftResponse])
def list_draft_payments(
    series: Optional[str] = Query(
        None, description="Restrict results to a single payment series"
    ),
    db: Session = Depends(get_db),
):
    """Return every active draft payment, optionally filtered by series.

    Each row is enriched with its contract title/amount, employer name,
    university name, and a running ``employer_balance_after`` computed
    across the returned set (§ ``_compute_balances_after``) — all via one
    joined query plus one balance calculation per distinct employer/year
    pair, never one query per row.
    """
    query = _enriched_payment_query(db).filter(
        Payment.status == "Draft",
        Payment.is_deleted == False,
    )
    if series:
        query = query.filter(Payment.series == series)

    rows = query.order_by(Payment.tracking_code).all()
    balances_after = _compute_balances_after(db, rows)
    return [
        _to_draft_response(
            payment,
            contract,
            employer,
            university,
            balance_after=balances_after.get(payment.tracking_code),
        )
        for payment, contract, employer, university in rows
    ]


@router.delete("/draft/{tracking_code}", response_model=DraftDeleteResponse)
def delete_draft_payment(
    tracking_code: str,
    db: Session = Depends(get_db),
):
    """
    Remove one draft payment (soft-delete, per the system-wide rule).

    Only ``Draft``-status rows can be removed this way; a ``Final``
    payment is not touched by this endpoint even if the tracking code
    matches.
    """
    draft = (
        db.query(Payment)
        .filter(
            Payment.tracking_code == tracking_code,
            Payment.status == "Draft",
            Payment.is_deleted == False,
        )
        .first()
    )
    if draft is None:
        raise HTTPException(
            status_code=404,
            detail=f"پیش‌نویس پرداخت با کد رهگیری '{tracking_code}' یافت نشد.",
        )

    draft.is_deleted = True
    db.commit()

    return DraftDeleteResponse(
        message="پیش‌نویس با موفقیت حذف شد.",
        tracking_code=tracking_code,
    )


@router.post("/finalize-batch", response_model=FinalizeBatchResponse)
def finalize_batch(
    request: FinalizeBatchRequest,
    db: Session = Depends(get_db),
):
    """
    Confirm every active draft in a series, moving it to ``Final`` status.

    Purely a status transition: ``calculate_real_balance`` already counts
    ``Draft`` and ``Final`` payments identically, so finalizing a series
    does not change any employer's projected balance — the funds were
    already reserved the moment each draft was created. Finalizing a
    series with no matching drafts succeeds with ``finalized_count: 0``
    rather than erroring, so a duplicate click is harmless.

    Returns the full enriched records for the finalized batch (not just
    the count), so the frontend can build an Excel export from the
    response alone without a follow-up ``GET`` call.
    """
    try:
        drafts = (
            db.query(Payment)
            .filter(
                Payment.series == request.series,
                Payment.status == "Draft",
                Payment.is_deleted == False,
            )
            .all()
        )
        finalized_tracking_codes = [draft.tracking_code for draft in drafts]
        for draft in drafts:
            draft.status = "Final"
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"خطا در نهایی‌سازی لیست پرداخت: {exc}",
        )

    finalized_payments: List[PaymentDraftResponse] = []
    if finalized_tracking_codes:
        rows = (
            _enriched_payment_query(db)
            .filter(Payment.tracking_code.in_(finalized_tracking_codes))
            .order_by(Payment.tracking_code)
            .all()
        )
        balances_after = _compute_balances_after(db, rows)
        finalized_payments = [
            _to_draft_response(
                payment,
                contract,
                employer,
                university,
                balance_after=balances_after.get(payment.tracking_code),
            )
            for payment, contract, employer, university in rows
        ]

    return FinalizeBatchResponse(
        message=(
            f"{len(drafts)} پرداخت با موفقیت نهایی شد."
            if drafts
            else "هیچ پیش‌نویس فعالی برای این سری یافت نشد."
        ),
        series=request.series,
        finalized_count=len(drafts),
        finalized_payments=finalized_payments,
    )


## File: api\v1\endpoints\researchers.py
------------------------------
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import get_db
from models.researchers import Researcher
from models.university import University
from schemas.researcher_schema import ResearcherCreate, ResearcherCreated

router = APIRouter(
    prefix="/researchers",
    tags=["Researchers"],
)


@router.get("/lookup", summary="Researcher lookup for dropdowns")
def researcher_lookup(db: Session = Depends(get_db)):
    """Return national_id + name for active researchers."""
    rows = db.query(Researcher.national_code, Researcher.full_name).filter(
        Researcher.is_deleted == False,
    ).order_by(Researcher.full_name).all()
    return [{"national_id": nc, "name": name} for nc, name in rows]


@router.post("/", response_model=ResearcherCreated, status_code=201)
def create_researcher(req: ResearcherCreate, db: Session = Depends(get_db)):
    """
    Register a new researcher (فناور).

    Business rule: a unique national_code is enforced before insert (including
    soft-deleted records). The model requires full_name, which is built by
    concatenating first_name and last_name.
    """
    existing = db.query(Researcher).filter(
        Researcher.national_code == req.national_code,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="خطا: فناور با این کد ملی قبلاً در سیستم ثبت شده است.",
        )

    university = db.query(University).filter(
        University.national_id == req.university_id,
        University.is_deleted == False,
    ).first()
    if not university:
        raise HTTPException(
            status_code=404,
            detail=f"دانشگاه/موسسه‌ای با شناسه ملی '{req.university_id}' یافت نشد.",
        )

    full_name = f"{req.first_name.strip()} {req.last_name.strip()}"

    researcher = Researcher(
        national_code=req.national_code,
        first_name=req.first_name.strip(),
        last_name=req.last_name.strip(),
        full_name=full_name,
        mobile=req.mobile,
        email=req.email,
        academic_rank=req.academic_rank,
        education_level=req.education_level,
        researcher_type=req.researcher_type,
        university_id=req.university_id,
        status=req.status,
        is_deleted=False,
    )
    db.add(researcher)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="خطا: فناور با این کد ملی قبلاً در سیستم ثبت شده است.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving researcher: {e}")
    db.refresh(researcher)

    return ResearcherCreated(
        national_code=researcher.national_code,
        full_name=researcher.full_name,
        university_id=researcher.university_id,
        academic_rank=researcher.academic_rank,
        education_level=researcher.education_level,
        researcher_type=researcher.researcher_type,
        status=researcher.status,
    )


## File: api\v1\endpoints\universities.py
------------------------------
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import get_db
from models.university import University
from schemas.university_schema import UniversityCreate, UniversityCreated

router = APIRouter(
    prefix="/universities",
    tags=["Universities"],
)


@router.get("/lookup", summary="University lookup for dropdowns")
def university_lookup(db: Session = Depends(get_db)):
    """Return national_id + name for active universities."""
    rows = db.query(University.national_id, University.name).filter(
        University.is_deleted == False,
    ).order_by(University.name).all()
    return [{"national_id": nid, "name": name} for nid, name in rows]


@router.post("/", response_model=UniversityCreated, status_code=201)
def create_university(payload: UniversityCreate, db: Session = Depends(get_db)):
    """
    Register a new university / executing institution.

    Business rule: a unique national_id is enforced before insert (including
    soft-deleted records) to avoid re-registration conflicts.
    """
    existing = db.query(University).filter(
        University.national_id == payload.national_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="خطا: موسسه‌ای با این شناسه ملی قبلاً در سیستم ثبت شده است.",
        )

    university = University(
        national_id=payload.national_id,
        name=payload.name,
        province=payload.province,
        university_type=payload.university_type,
        status="Active" if payload.is_active else "Inactive",
        is_deleted=False,
    )
    db.add(university)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="خطا: موسسه‌ای با این شناسه ملی قبلاً در سیستم ثبت شده است.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving university: {e}")
    db.refresh(university)

    return UniversityCreated(
        national_id=university.national_id,
        name=university.name,
        province=university.province,
        university_type=university.university_type,
        status=university.status,
    )


## File: api\v1\endpoints\__init__.py
------------------------------


## File: core\database.py
------------------------------
"""Database core for the SATE financial system.

Configures the SQLAlchemy engine, session factory, declarative ``Base`` class,
and the shared :class:`SoftDeleteMixin` used by every domain model to support
non-destructive (soft) deletion of records.

Soft-delete convention
----------------------
Every model inherits from both :data:`Base` and :class:`SoftDeleteMixin`.
Records are flagged via ``is_deleted`` rather than physically removed, which
preserves audit history and referential integrity across the dataset.
"""

import os

from sqlalchemy import Boolean, Column, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Please configure it in .env.")

# Create engine with connection pooling settings
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class SoftDeleteMixin:
    """Mixin providing non-destructive (soft) deletion support.

    Columns
    -------
    is_deleted : bool
        Flag indicating whether the row is logically deleted. ``False`` means
        the record is live; ``True`` means it has been soft-deleted and should
        be excluded from active result sets. Indexed for query performance.
    """

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)


def get_db():
    """Yield a scoped database session and ensure it is closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


## File: core\date_helper.py
------------------------------
"""Shared strict date conversion helpers."""

from datetime import date

import jdatetime


def parse_strict_jalali_date(date_str: str) -> date:
    """
    Parse a Jalali date using strict calendar validation.

    Both ``YYYY/MM/DD`` and ``YYYY-MM-DD`` inputs are accepted. Invalid month
    lengths, leap-day values, and malformed inputs raise ``ValueError``.

    Args:
        date_str: Jalali date text entered by a user or loaded from a file.

    Returns:
        The equivalent Gregorian ``date`` value.

    Raises:
        TypeError: If ``date_str`` is not a string.
        ValueError: If the input is empty, malformed, or invalid in the Jalali
            calendar.
    """
    if not isinstance(date_str, str):
        raise TypeError("Jalali date value must be a string.")

    clean_str = date_str.strip().replace("-", "/")
    if not clean_str:
        raise ValueError("Jalali date value cannot be empty.")

    parsed_date = jdatetime.datetime.strptime(clean_str, "%Y/%m/%d").date()
    return parsed_date.togregorian()


def parse_strict_jalali_iso(date_str: str) -> str:
    """
    Parse a Jalali date securely and return Gregorian ISO format.

    Args:
        date_str: Jalali date text in ``YYYY/MM/DD`` or ``YYYY-MM-DD`` format.

    Returns:
        Gregorian date text in ISO ``YYYY-MM-DD`` format.
    """
    return parse_strict_jalali_date(date_str).isoformat()


## File: dashboard\app.py
------------------------------
import io
import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import func
from sqlalchemy.orm import Session

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from models.contract import Contract
from models.deposits import AnnualMandate, DepositReceipt
from models.employer import Employer
from models.payment import Payment
from models.transfer import CreditTransfer
from services.financial_engine import get_all_employers_financials

FINANCIAL_COLUMNS = [
    "mandated_amount",
    "deposit_amount",
    "payment_amount",
    "transfer_in",
    "transfer_out",
    "balance",
]

TRANSFER_OUT_LABEL = "انتقال مانده طی اصلاحیه تبصره 2 ماده 5"
COLUMN_LABELS = {
    "year": "سال مالی",
    "mandated_amount": "اعتبار تکلیفی",
    "deposit_amount": "مجموع واریزی",
    "payment_amount": "هزینه کرد",
    "transfer_in": "انتقال ورودی",
    "transfer_out": TRANSFER_OUT_LABEL,
    "balance": "مانده واقعی",
}
DISPLAY_COLUMNS = [
    "year",
    "mandated_amount",
    "deposit_amount",
    "payment_amount",
    "transfer_in",
    "transfer_out",
    "balance",
]


def get_employer_financials(db: Session, employer_code: str):
    """Fetch and aggregate financial data for a specific employer across all years."""
    employer = db.query(Employer).filter(Employer.classification_code == employer_code).first()
    if not employer:
        return pd.DataFrame()

    if employer.employer_type == "Mother":
        codes_to_include = [employer_code]
        subsidiaries = db.query(Employer.classification_code).filter(
            Employer.parent_code == employer_code,
            Employer.is_deleted == False,
        ).all()
        codes_to_include.extend([s[0] for s in subsidiaries])
    else:
        codes_to_include = [employer_code]

    mandates_query = db.query(
        AnnualMandate.fiscal_year.label("year"),
        func.sum(AnnualMandate.mandated_amount).label("mandated_amount"),
    ).filter(
        AnnualMandate.employer_code.in_(codes_to_include),
        AnnualMandate.is_deleted == False,
    ).group_by(AnnualMandate.fiscal_year)
    df_mandates = pd.read_sql(mandates_query.statement, db.bind)

    deposits_query = db.query(
        DepositReceipt.fiscal_year.label("year"),
        func.sum(DepositReceipt.deposit_amount).label("deposit_amount"),
    ).filter(
        DepositReceipt.employer_code.in_(codes_to_include),
        DepositReceipt.is_deleted == False,
    ).group_by(DepositReceipt.fiscal_year)
    df_deposits = pd.read_sql(deposits_query.statement, db.bind)

    payments_query = db.query(
        Payment.funding_year.label("year"),
        func.sum(Payment.amount).label("payment_amount"),
    ).join(
        Contract, Payment.contract_tracking_code == Contract.tracking_code
    ).filter(
        Contract.employer_code.in_(codes_to_include),
        Payment.is_deleted == False,
        Contract.is_deleted == False,
    ).group_by(Payment.funding_year)
    df_payments = pd.read_sql(payments_query.statement, db.bind)

    transfers_in_query = db.query(
        CreditTransfer.fiscal_year.label("year"),
        func.sum(CreditTransfer.amount).label("transfer_in"),
    ).filter(
        CreditTransfer.destination_employer_code.in_(codes_to_include),
        CreditTransfer.is_deleted == False,
    ).group_by(CreditTransfer.fiscal_year)
    df_transfers_in = pd.read_sql(transfers_in_query.statement, db.bind)

    transfers_out_query = db.query(
        CreditTransfer.fiscal_year.label("year"),
        func.sum(CreditTransfer.amount).label("transfer_out"),
    ).filter(
        CreditTransfer.source_employer_code.in_(codes_to_include),
        CreditTransfer.is_deleted == False,
    ).group_by(CreditTransfer.fiscal_year)
    df_transfers_out = pd.read_sql(transfers_out_query.statement, db.bind)

    dfs = [df_mandates, df_deposits, df_payments, df_transfers_in, df_transfers_out]
    df_merged = dfs[0]
    for df in dfs[1:]:
        df_merged = df_merged.merge(df, on="year", how="outer")
    df_merged = df_merged.fillna(0)

    df_merged["balance"] = (
        df_merged["deposit_amount"]
        + df_merged["transfer_in"]
        - df_merged["payment_amount"]
        - df_merged["transfer_out"]
    )
    df_merged = df_merged.sort_values("year")
    return df_merged


def render_kpi_card(year, mandated, adj_dep, adj_pay):
    """Render a styled HTML KPI card for a single fiscal year."""
    dep_pct = min(100, (adj_dep / mandated * 100) if mandated > 0 else 0)
    pay_pct = min(100, (adj_pay / mandated * 100) if mandated > 0 else 0)

    html_content = f"""
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); direction: rtl; font-family: 'Vazirmatn', sans-serif;">
        <h4 style="text-align: center; color: #111827;">سال {to_persian_numbers(int(year))}</h4>
        <div style="font-size: 14px; margin-bottom: 10px;">اعتبار تکلیفی: {to_persian_numbers(int(mandated))}</div>
        <div style="font-size: 14px; margin-bottom: 5px;">واریزی تعدیل‌شده: {to_persian_numbers(int(adj_dep))}</div>
        <div style="background-color: #e5e7eb; border-radius: 4px; height: 8px; margin-bottom: 15px;">
            <div style="width: {dep_pct}%; background-color: #10B981; height: 8px; border-radius: 4px;"></div>
        </div>
        <div style="font-size: 14px; margin-bottom: 5px;">هزینه‌کرد تعدیل‌شده: {to_persian_numbers(int(adj_pay))}</div>
        <div style="background-color: #e5e7eb; border-radius: 4px; height: 8px;">
            <div style="width: {pay_pct}%; background-color: #3B82F6; height: 8px; border-radius: 4px;"></div>
        </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)


def to_persian_numbers(text):
    """Convert English digits to Persian digits and format numbers with thousand separators."""
    persian_digits = {
        "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
        "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
    }
    if isinstance(text, (int, float)):
        text = f"{int(text):,}"
    else:
        text = str(text)
    for eng, per in persian_digits.items():
        text = text.replace(eng, per)
    return text


def get_active_employers(db: Session):
    """Fetch all active employers for dropdown."""
    return db.query(Employer).filter(
        Employer.status == "Active",
        Employer.is_deleted == False,
    ).order_by(Employer.name).all()


def to_excel(df: pd.DataFrame) -> bytes:
    """Convert dataframe to Excel bytes for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Financial Report")
    output.seek(0)
    return output.getvalue()


def add_adjusted_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["adjusted_deposits"] = df["deposit_amount"] + df["transfer_in"]
    df["adjusted_payments"] = df["payment_amount"] + df["transfer_out"]
    return df


def convert_financials_to_millions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    existing_financial_cols = [col for col in FINANCIAL_COLUMNS if col in df.columns]
    df[existing_financial_cols] = df[existing_financial_cols] / 1_000_000
    return df


def million_rials_label():
    st.markdown(
        "<p style='text-align: center; font-size: 14px; color: gray;'>(ارقام بر حسب میلیون ریال)</p>",
        unsafe_allow_html=True,
    )


def persian_tick_values(values, steps=5):
    values = pd.Series(values).dropna()
    if values.empty:
        return [0], ["۰"]

    min_value = min(0, float(values.min()))
    max_value = max(0, float(values.max()))
    if min_value == max_value:
        return [0], ["۰"]

    tickvals = [min_value + (max_value - min_value) * i / steps for i in range(steps + 1)]
    ticktext = [to_persian_numbers(int(v)) for v in tickvals]
    return tickvals, ticktext


def render_yearly_kpi_cards(df: pd.DataFrame):
    years = sorted(df["year"].unique())
    kpi_cols = st.columns(len(years))

    for idx, year in enumerate(years):
        year_data = df[df["year"] == year].iloc[0]
        with kpi_cols[idx]:
            render_kpi_card(
                year,
                year_data["mandated_amount"],
                year_data["adjusted_deposits"],
                year_data["adjusted_payments"],
            )


def render_grouped_bar_chart(chart_data: pd.DataFrame):
    chart_data = chart_data.sort_values("year")
    years_persian = [to_persian_numbers(int(y)) for y in chart_data["year"]]
    tickvals, ticktext = persian_tick_values(pd.concat([
        chart_data["mandated_amount"],
        chart_data["adjusted_deposits"],
        chart_data["adjusted_payments"],
    ]))

    fig_grouped = go.Figure()
    fig_grouped.add_trace(go.Bar(
        x=years_persian,
        y=chart_data["mandated_amount"],
        name="اعتبار تکلیفی",
        marker_color="#757575",
        text=[to_persian_numbers(int(v)) for v in chart_data["mandated_amount"]],
        textposition="outside",
        textfont=dict(family="Vazirmatn", size=11),
    ))
    fig_grouped.add_trace(go.Bar(
        x=years_persian,
        y=chart_data["adjusted_deposits"],
        name="واریزی تعدیل‌شده",
        marker_color="#4CAF50",
        text=[to_persian_numbers(int(v)) for v in chart_data["adjusted_deposits"]],
        textposition="outside",
        textfont=dict(family="Vazirmatn", size=11),
    ))
    fig_grouped.add_trace(go.Bar(
        x=years_persian,
        y=chart_data["adjusted_payments"],
        name="هزینه تعدیل‌شده",
        marker_color="#2196F3",
        text=[to_persian_numbers(int(v)) for v in chart_data["adjusted_payments"]],
        textposition="outside",
        textfont=dict(family="Vazirmatn", size=11),
    ))
    fig_grouped.update_layout(
        barmode="group",
        font=dict(family="Vazirmatn", size=14),
        title=dict(
            text="مقایسه اعتبار تکلیفی، واریزی تعدیل‌شده و هزینه تعدیل‌شده",
            x=0.5,
            xanchor="center",
            font=dict(family="Vazirmatn", size=18),
        ),
        title_font=dict(family="Vazirmatn"),
        xaxis=dict(
            title="سال مالی",
            tickfont=dict(family="Vazirmatn", size=13),
            title_font=dict(family="Vazirmatn"),
        ),
        yaxis=dict(
            title="مبلغ (میلیون ریال)",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickfont=dict(family="Vazirmatn", size=12),
            title_font=dict(family="Vazirmatn"),
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(family="Vazirmatn", size=13),
        ),
        legend_font=dict(family="Vazirmatn"),
        height=600,
        margin=dict(l=60, r=40, t=80, b=120),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_grouped, width="stretch", theme=None)


def render_waterfall_chart(chart_data: pd.DataFrame):
    tot_dep = chart_data["adjusted_deposits"].sum()
    tot_pay = chart_data["adjusted_payments"].sum()
    tot_bal = chart_data["balance"].sum()

    waterfall_labels = [" واریزی تعدیل‌شده", " هزینه تعدیل‌شده", " مانده واقعی"]
    waterfall_values = [tot_dep, -tot_pay, tot_bal]
    cumulative_values = [0, tot_dep, tot_dep - tot_pay, tot_bal]
    tickvals, ticktext = persian_tick_values(cumulative_values)

    fig_waterfall = go.Figure(go.Waterfall(
        name="جریان منابع و مصارف",
        orientation="v",
        measure=["relative", "relative", "total"],
        x=waterfall_labels,
        y=waterfall_values,
        text=[to_persian_numbers(int(v)) for v in waterfall_values],
        textposition="outside",
        textfont=dict(family="Vazirmatn", size=12),
        connector=dict(line=dict(color="#9CA3AF")),
        increasing=dict(marker=dict(color="#10B981")),
        decreasing=dict(marker=dict(color="#EF4444")),
        totals=dict(marker=dict(color="#3B82F6")),
    ))
    fig_waterfall.update_layout(
        font=dict(family="Vazirmatn", size=14),
        title=dict(
            text="نمای تجمعی جریان منابع و مصارف",
            x=0.5,
            xanchor="center",
            font=dict(family="Vazirmatn", size=18),
        ),
        title_font=dict(family="Vazirmatn"),
        xaxis=dict(
            tickfont=dict(family="Vazirmatn", size=13),
            title_font=dict(family="Vazirmatn"),
        ),
        yaxis=dict(
            title="مبلغ (میلیون ریال)",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickfont=dict(family="Vazirmatn", size=12),
            title_font=dict(family="Vazirmatn"),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(family="Vazirmatn", size=13),
        ),
        height=520,
        margin=dict(l=60, r=40, t=80, b=120),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_waterfall, width="stretch", theme=None)


def render_detailed_table_and_download(df: pd.DataFrame, file_name: str):
    st.subheader("📋 جدول تفصیلی به تفکیک سال")
    million_rials_label()

    df_display = df[DISPLAY_COLUMNS].copy().rename(columns=COLUMN_LABELS)
    df_display[COLUMN_LABELS["year"]] = df_display[COLUMN_LABELS["year"]].apply(to_persian_numbers)
    for col_key, col_label in COLUMN_LABELS.items():
        if col_key != "year":
            df_display[col_label] = df_display[col_label].apply(to_persian_numbers)

    st.table(df_display)

    df_excel = df[DISPLAY_COLUMNS].copy().rename(columns=COLUMN_LABELS)
    st.download_button(
        label="📥 دانلود گزارش به صورت اکسل",
        data=to_excel(df_excel),
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_tab1(db: Session, employers):
    employer_options = {emp.classification_code: f"{emp.name} ({emp.classification_code})" for emp in employers}
    employer_keys = list(employer_options.keys())
    default_index = employer_keys.index("231500") if "231500" in employer_keys else 0

    selected_code = st.selectbox(
        "انتخاب مشمول:",
        options=employer_keys,
        format_func=lambda x: employer_options[x],
        index=default_index,
    )

    if not selected_code:
        return

    selected_employer = next(emp for emp in employers if emp.classification_code == selected_code)

    st.subheader(f"اطلاعات مشمول: {selected_employer.name}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**کد طبقه‌بندی:** {selected_employer.classification_code}")
    with col2:
        st.info(f"**استان:** {selected_employer.province}")
    with col3:
        st.info(f"**سازمان بالادست:** {selected_employer.upper_organization}")

    st.markdown("---")

    with st.spinner("در حال بارگذاری اطلاعات مالی..."):
        df = get_employer_financials(db, selected_code)

    df = df[df["year"] >= 1402]
    if df.empty:
        st.warning("هیچ داده مالی برای این مشمول از سال ۱۴۰۲ به بعد یافت نشد.")
        return

    df = add_adjusted_columns(convert_financials_to_millions(df))

    st.subheader("🔑 شاخص‌های کلیدی")
    million_rials_label()
    render_yearly_kpi_cards(df)

    st.markdown("---")
    render_detailed_table_and_download(df, f"financial_report_v2_{selected_code}.xlsx")

    st.markdown("---")
    st.subheader("📊 تحلیل و نمودار")
    million_rials_label()
    render_grouped_bar_chart(df)
    render_waterfall_chart(df)


def render_top10_employers_chart(df_all: pd.DataFrame):
    st.markdown("### 📊 ۱۰ مشمول برتر بر اساس میزان واریزی")

    top10 = df_all.groupby(
        ["employer_code", "employer_name"], as_index=False
    )["deposit_amount"].sum().nlargest(10, "deposit_amount")

    tickvals, ticktext = persian_tick_values(top10["deposit_amount"])
    fig_top10 = go.Figure(go.Bar(
        x=top10["deposit_amount"],
        y=top10["employer_name"],
        orientation="h",
        text=top10["deposit_amount"].apply(lambda v: to_persian_numbers(int(v))),
        textposition="auto",
        marker_color="#2196F3",
        name="مجموع واریزی",
    ))
    fig_top10.update_layout(
        font=dict(family="Vazirmatn", size=14),
        xaxis=dict(
            title="مبلغ واریزی (میلیون ریال)",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            tickfont=dict(family="Vazirmatn", size=12),
            title_font=dict(family="Vazirmatn"),
        ),
        yaxis=dict(
            title="",
            autorange="reversed",
            tickfont=dict(family="Vazirmatn", size=12),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(family="Vazirmatn", size=13),
        ),
        height=500,
        margin=dict(l=20, r=20, t=40, b=100),
    )
    st.plotly_chart(fig_top10, width="stretch", theme=None)


def render_global_excel_download(df_all: pd.DataFrame):
    df_export = df_all.copy().rename(columns={
        "employer_code": "کد مشمول",
        "employer_name": "نام مشمول",
        "year": "سال مالی",
        "mandated_amount": "اعتبار تکلیفی",
        "deposit_amount": "مجموع واریزی",
        "payment_amount": "هزینه کرد",
        "transfer_in": "انتقال ورودی",
        "transfer_out": "انتقال خروجی",
        "balance": "مانده واقعی",
    })

    st.download_button(
        label="📥 دانلود گزارش جامع کل مشمولین (اکسل)",
        data=to_excel(df_export),
        file_name="financial_report_all_employers.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_tab2(db: Session):
    st.subheader("🏢 نمای کلان - خلاصه مدیریتی")

    with st.spinner("در حال بارگذاری اطلاعات کلان..."):
        df_all = get_all_employers_financials(db)

    if df_all.empty:
        st.warning("هیچ داده مالی در سیستم یافت نشد.")
        return

    df_all = df_all[df_all["year"] >= 1402]
    if df_all.empty:
        st.warning("هیچ داده مالی از سال ۱۴۰۲ به بعد یافت نشد.")
        return

    df_all = convert_financials_to_millions(df_all)
    df_macro_yearly = df_all.groupby("year", as_index=False)[FINANCIAL_COLUMNS].sum()
    df_macro_yearly = add_adjusted_columns(df_macro_yearly)

    st.subheader("🔑 شاخص‌های کلیدی")
    million_rials_label()
    render_yearly_kpi_cards(df_macro_yearly)

    st.markdown("---")
    st.subheader("📊 تحلیل و نمودار")
    million_rials_label()
    render_grouped_bar_chart(df_macro_yearly)
    render_waterfall_chart(df_macro_yearly)

    st.markdown("---")
    render_top10_employers_chart(df_all)

    st.markdown("---")
    render_global_excel_download(df_all)


def render_dashboard():
    """Render the main management dashboard (used as a st.Page target)."""
    # ─── Main Title ───
    st.markdown("<h1 style='text-align: center;'>📊 داشبورد مدیریتی ساتع - تراز مشمولین</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>(داده‌های مالی از سال ۱۴۰۲)</h3>", unsafe_allow_html=True)

    # ─── Aggressive CSS: Vazirmatn font + full RTL override ───
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    html, body, [class*="css"], * {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    h1, h2, h3, .stHeadingContainer { text-align: center !important; direction: rtl; }
    table, th, td, .stTable, [data-testid="stTable"] * {
        font-family: 'Vazirmatn', sans-serif !important;
        font-size: 15px !important;
        text-align: center !important;
        direction: rtl !important;
    }
    .stPlotlyChart, .js-plotly-plot, .plotly {
        direction: ltr !important;
    }
    th { background-color: #f0f2f6 !important; border-bottom: 2px solid #4a4a4a !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("---")

    db = SessionLocal()
    try:
        employers = get_active_employers(db)
        if not employers:
            st.warning("هیچ مشمولی فعال در سیستم یافت نشد.")
            return

        tab1, tab2 = st.tabs(["ترازنامه مشمولین", "نمای کلان - Executive Summary"])
        with tab1:
            render_tab1(db, employers)
        with tab2:
            render_tab2(db)
    finally:
        db.close()


def _inject_global_css():
    """Global CSS: aggressive RTL override for Streamlit internal containers."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    /* Force RTL on main containers and text inputs */
    .block-container, .stTextInput, .stNumberInput, .stSelectbox, p, div {
        direction: rtl !important;
        text-align: right !important;
    }
    /* Fix sidebar text alignment */
    [data-testid="stSidebarNav"] span {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.05rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # 1. MUST be the first Streamlit command executed in the file.
    st.set_page_config(page_title="سامانه مالی ساتع", layout="wide")

    # 2. Define the pages via the st.Page API.
    dash_page = st.Page(render_dashboard, title="داشبورد اصلی", icon="📊", default=True)
    batch_payments_page = st.Page("views/batch_payments_page.py", title="ثبت دسته‌ای پرداخت", icon="📝")
    contract_entry_page = st.Page("views/contract_entry_page.py", title="ثبت قرارداد جدید", icon="📄")
    contract_edit_page = st.Page("views/contract_edit_page.py", title="جستجو و ویرایش قرارداد", icon="✏️")
    university_entry_page = st.Page("views/university_entry_page.py", title="ثبت موسسه مجری", icon="🏫")
    researcher_entry_page = st.Page("views/researcher_entry_page.py", title="ثبت اطلاعات فناور", icon="🧑‍🔬")

    # 3. Group and initialize navigation.
    pg = st.navigation({
        "داشبوردهای مدیریتی": [dash_page],
        "فرم‌های ورود اطلاعات": [
            batch_payments_page,
            contract_entry_page,
            contract_edit_page,
            university_entry_page,
            researcher_entry_page,
        ],
    })

    # 4. Inject global CSS (RTL & Fonts) before rendering the active page.
    _inject_global_css()

    # 5. CRITICAL: Execute the navigation / render the active page.
    pg.run()


if __name__ == "__main__":
    main()


## File: dashboard\app_v2.py
------------------------------
import streamlit as st
import pandas as pd
import io
from sqlalchemy import func
from sqlalchemy.orm import Session
import sys
import os
import plotly.graph_objects as go

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from models.employer import Employer
from models.deposits import AnnualMandate, DepositReceipt
from models.payment import Payment
from models.contract import Contract
from models.transfer import CreditTransfer


def to_persian_numbers(text):
    """Convert English digits to Persian digits and format numbers with thousand separators."""
    persian_digits = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    if isinstance(text, (int, float)):
        text = f"{int(text):,}"
    else:
        text = str(text)
    for eng, per in persian_digits.items():
        text = text.replace(eng, per)
    return text


def get_active_employers(db: Session):
    """Fetch all active employers for dropdown."""
    employers = db.query(Employer).filter(
        Employer.status == 'Active',
        Employer.is_deleted == False
    ).order_by(Employer.name).all()
    return employers


def get_employer_financials(db: Session, employer_code: str):
    """Fetch and aggregate financial data for a specific employer across all years."""
    employer = db.query(Employer).filter(Employer.classification_code == employer_code).first()
    if not employer:
        return pd.DataFrame()

    if employer.employer_type == 'Mother':
        codes_to_include = [employer_code]
        subsidiaries = db.query(Employer.classification_code).filter(
            Employer.parent_code == employer_code,
            Employer.is_deleted == False
        ).all()
        codes_to_include.extend([s[0] for s in subsidiaries])
    else:
        codes_to_include = [employer_code]

    mandates_query = db.query(
        AnnualMandate.fiscal_year.label('year'),
        func.sum(AnnualMandate.mandated_amount).label('mandated_amount')
    ).filter(
        AnnualMandate.employer_code.in_(codes_to_include),
        AnnualMandate.is_deleted == False
    ).group_by(AnnualMandate.fiscal_year)
    df_mandates = pd.read_sql(mandates_query.statement, db.bind)

    deposits_query = db.query(
        DepositReceipt.fiscal_year.label('year'),
        func.sum(DepositReceipt.deposit_amount).label('deposit_amount')
    ).filter(
        DepositReceipt.employer_code.in_(codes_to_include),
        DepositReceipt.is_deleted == False
    ).group_by(DepositReceipt.fiscal_year)
    df_deposits = pd.read_sql(deposits_query.statement, db.bind)

    payments_query = db.query(
        Payment.funding_year.label('year'),
        func.sum(Payment.amount).label('payment_amount')
    ).join(
        Contract, Payment.contract_tracking_code == Contract.tracking_code
    ).filter(
        Contract.employer_code.in_(codes_to_include),
        Payment.is_deleted == False,
        Contract.is_deleted == False
    ).group_by(Payment.funding_year)
    df_payments = pd.read_sql(payments_query.statement, db.bind)

    transfers_in_query = db.query(
        CreditTransfer.fiscal_year.label('year'),
        func.sum(CreditTransfer.amount).label('transfer_in')
    ).filter(
        CreditTransfer.destination_employer_code.in_(codes_to_include),
        CreditTransfer.is_deleted == False
    ).group_by(CreditTransfer.fiscal_year)
    df_transfers_in = pd.read_sql(transfers_in_query.statement, db.bind)

    transfers_out_query = db.query(
        CreditTransfer.fiscal_year.label('year'),
        func.sum(CreditTransfer.amount).label('transfer_out')
    ).filter(
        CreditTransfer.source_employer_code.in_(codes_to_include),
        CreditTransfer.is_deleted == False
    ).group_by(CreditTransfer.fiscal_year)
    df_transfers_out = pd.read_sql(transfers_out_query.statement, db.bind)

    dfs = [df_mandates, df_deposits, df_payments, df_transfers_in, df_transfers_out]
    df_merged = dfs[0]
    for df in dfs[1:]:
        df_merged = df_merged.merge(df, on='year', how='outer')
    df_merged = df_merged.fillna(0)

    df_merged['balance'] = (
        df_merged['deposit_amount'] +
        df_merged['transfer_in'] -
        df_merged['payment_amount'] -
        df_merged['transfer_out']
    )
    df_merged = df_merged.sort_values('year')
    return df_merged


def format_million_value(value) -> str:
    """Format a million-scale amount with commas and Persian digits."""
    return to_persian_numbers(round(value))


def render_kpi_card(year, mandated, adj_dep, adj_pay):
    """Render a styled HTML KPI card for a single fiscal year."""
    dep_pct = min(100, (adj_dep / mandated * 100) if mandated > 0 else 0)
    pay_pct = min(100, (adj_pay / mandated * 100) if mandated > 0 else 0)

    html_content = f'''
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); direction: rtl; font-family: 'Vazirmatn', sans-serif;">
        <h4 style="text-align: center; color: #111827;">سال {to_persian_numbers(int(year))}</h4>
        <div style="font-size: 14px; margin-bottom: 10px;">اعتبار تکلیفی: {to_persian_numbers(int(mandated))}</div>
        <div style="font-size: 14px; margin-bottom: 5px;">واریزی تعدیل‌شده: {to_persian_numbers(int(adj_dep))}</div>
        <div style="background-color: #e5e7eb; border-radius: 4px; height: 8px; margin-bottom: 15px;">
            <div style="width: {dep_pct}%; background-color: #10B981; height: 8px; border-radius: 4px;"></div>
        </div>
        <div style="font-size: 14px; margin-bottom: 5px;">هزینه‌کرد تعدیل‌شده: {to_persian_numbers(int(adj_pay))}</div>
        <div style="background-color: #e5e7eb; border-radius: 4px; height: 8px;">
            <div style="width: {pay_pct}%; background-color: #3B82F6; height: 8px; border-radius: 4px;"></div>
        </div>
    </div>
    '''
    st.markdown(html_content, unsafe_allow_html=True)


def to_excel(df: pd.DataFrame) -> bytes:
    """Convert dataframe to Excel bytes for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Financial Report')
    output.seek(0)
    return output.getvalue()


def main():
    st.set_page_config(
        page_title="داشبورد ساتع - نسخه پیشرفته",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ─── Main Title ───
    st.markdown("<h1 style='text-align: center;'>📊 داشبورد مدیریتی ساتع - تراز مشمولین</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>(داده‌های مالی از سال ۱۴۰۲)</h3>", unsafe_allow_html=True)

    # ─── Aggressive CSS: Vazirmatn font + full RTL override ───
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    html, body, [class*="css"], * {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    h1, h2, h3, .stHeadingContainer { text-align: center !important; direction: rtl; }
    table, th, td, .stTable, [data-testid="stTable"] * {
        font-family: 'Vazirmatn', sans-serif !important;
        font-size: 15px !important;
        text-align: center !important;
        direction: rtl !important;
    }
    .stPlotlyChart, .js-plotly-plot, .plotly {
        direction: ltr !important;
    }
    th { background-color: #f0f2f6 !important; border-bottom: 2px solid #4a4a4a !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("---")

    db = SessionLocal()

    try:
        employers = get_active_employers(db)

        if not employers:
            st.warning("هیچ مشمولی فعال در سیستم یافت نشد.")
            return

        # ─── Employer Selection ───
        employer_options = {emp.classification_code: f"{emp.name} ({emp.classification_code})" for emp in employers}
        employer_keys = list(employer_options.keys())

        default_index = 0
        if '231500' in employer_keys:
            default_index = employer_keys.index('231500')

        selected_code = st.selectbox(
            "انتخاب مشمول:",
            options=employer_keys,
            format_func=lambda x: employer_options[x],
            index=default_index
        )

        if selected_code:
            selected_employer = next(emp for emp in employers if emp.classification_code == selected_code)

            # Employer info
            st.subheader(f"اطلاعات مشمول: {selected_employer.name}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**کد طبقه‌بندی:** {selected_employer.classification_code}")
            with col2:
                st.info(f"**استان:** {selected_employer.province}")
            with col3:
                st.info(f"**سازمان بالادست:** {selected_employer.upper_organization}")

            st.markdown("---")

            # Fetch data
            with st.spinner("در حال بارگذاری اطلاعات مالی..."):
                df = get_employer_financials(db, selected_code)

            # Filter: year >= 1402
            df = df[df['year'] >= 1402]

            if df.empty:
                st.warning("هیچ داده مالی برای این مشمول از سال ۱۴۰۲ به بعد یافت نشد.")
            else:
                # Convert to millions
                financial_cols = [
                    'mandated_amount', 'deposit_amount', 'payment_amount',
                    'transfer_in', 'transfer_out', 'balance'
                ]
                df[financial_cols] = df[financial_cols] / 1_000_000

                # Visualization-only adjusted columns
                df['adjusted_deposits'] = df['deposit_amount'] + df['transfer_in']
                df['adjusted_payments'] = df['payment_amount'] + df['transfer_out']

                # ─── KPIs: HTML Cards per Year ───
                st.subheader("🔑 شاخص‌های کلیدی")
                st.markdown(
                    "<p style='text-align: center; font-size: 14px; color: gray;'>(ارقام بر حسب میلیون ریال)</p>",
                    unsafe_allow_html=True
                )

                years = sorted(df['year'].unique())
                kpi_cols = st.columns(len(years))

                for idx, year in enumerate(years):
                    year_data = df[df['year'] == year].iloc[0]
                    mandated = year_data['mandated_amount']
                    adj_dep = year_data['adjusted_deposits']
                    adj_pay = year_data['adjusted_payments']

                    with kpi_cols[idx]:
                        render_kpi_card(year, mandated, adj_dep, adj_pay)

                st.markdown("---")

                # ─── Detailed Table ───
                st.subheader("📋 جدول تفصیلی به تفکیک سال")
                st.markdown(
                    "<p style='text-align: center; font-size: 14px; color: gray;'>(ارقام بر حسب میلیون ریال)</p>",
                    unsafe_allow_html=True
                )

                transfer_out_label = 'انتقال مانده طی اصلاحیه تبصره 2 ماده 5'
                column_labels = {
                    'year': 'سال مالی',
                    'mandated_amount': 'اعتبار تکلیفی',
                    'deposit_amount': 'مجموع واریزی',
                    'payment_amount': 'هزینه کرد',
                    'transfer_in': 'انتقال ورودی',
                    'transfer_out': transfer_out_label,
                    'balance': 'مانده واقعی'
                }
                display_cols = [
                    'year', 'mandated_amount', 'deposit_amount',
                    'payment_amount', 'transfer_in', 'transfer_out', 'balance'
                ]

                df_display = df[display_cols].copy().rename(columns=column_labels)
                df_display[column_labels['year']] = df_display[column_labels['year']].apply(to_persian_numbers)
                for col_key, col_label in column_labels.items():
                    if col_key != 'year':
                        df_display[col_label] = df_display[col_label].apply(to_persian_numbers)

                st.table(df_display)

                # Excel export (no adjusted columns)
                df_excel = df[display_cols].copy().rename(columns=column_labels)
                st.download_button(
                    label="📥 دانلود گزارش به صورت اکسل",
                    data=to_excel(df_excel),
                    file_name=f"financial_report_v2_{selected_code}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                st.markdown("---")

                # ─── Advanced Analytics: Grouped Bar Chart ───
                st.subheader("📊 تحلیل و نمودار")
                st.markdown(
                    "<p style='text-align: center; font-size: 14px; color: gray;'>(ارقام بر حسب میلیون ریال)</p>",
                    unsafe_allow_html=True
                )

                chart_data = df.sort_values('year')
                years_persian = [to_persian_numbers(int(y)) for y in chart_data['year']]

                grouped_max_value = max(
                    chart_data['mandated_amount'].max(),
                    chart_data['adjusted_deposits'].max(),
                    chart_data['adjusted_payments'].max(),
                    0
                )
                grouped_tickvals = [grouped_max_value * i / 5 for i in range(6)] if grouped_max_value > 0 else [0]
                grouped_ticktext = [to_persian_numbers(int(v)) for v in grouped_tickvals]

                fig_grouped = go.Figure()

                fig_grouped.add_trace(go.Bar(
                    x=years_persian,
                    y=chart_data['mandated_amount'],
                    name='اعتبار تکلیفی',
                    marker_color='#757575',
                    text=[to_persian_numbers(int(v)) for v in chart_data['mandated_amount']],
                    textposition='outside',
                    textfont=dict(family='Vazirmatn', size=11)
                ))

                fig_grouped.add_trace(go.Bar(
                    x=years_persian,
                    y=chart_data['adjusted_deposits'],
                    name='واریزی تعدیل‌شده',
                    marker_color='#4CAF50',
                    text=[to_persian_numbers(int(v)) for v in chart_data['adjusted_deposits']],
                    textposition='outside',
                    textfont=dict(family='Vazirmatn', size=11)
                ))

                fig_grouped.add_trace(go.Bar(
                    x=years_persian,
                    y=chart_data['adjusted_payments'],
                    name='هزینه تعدیل‌شده',
                    marker_color='#2196F3',
                    text=[to_persian_numbers(int(v)) for v in chart_data['adjusted_payments']],
                    textposition='outside',
                    textfont=dict(family='Vazirmatn', size=11)
                ))

                fig_grouped.update_layout(
                    barmode='group',
                    font=dict(family='Vazirmatn', size=14),
                    title=dict(
                        text='مقایسه اعتبار تکلیفی، واریزی تعدیل‌شده و هزینه تعدیل‌شده',
                        x=0.5,
                        xanchor='center',
                        font=dict(family='Vazirmatn', size=18)
                    ),
                    title_font=dict(family='Vazirmatn'),
                    xaxis=dict(
                        title='سال مالی',
                        tickfont=dict(family='Vazirmatn', size=13),
                        title_font=dict(family='Vazirmatn')
                    ),
                    yaxis=dict(
                        title='مبلغ (میلیون ریال)',
                        tickmode='array',
                        tickvals=grouped_tickvals,
                        ticktext=grouped_ticktext,
                        tickfont=dict(family='Vazirmatn', size=12),
                        title_font=dict(family='Vazirmatn')
                    ),
                    legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.15,
                        xanchor='center',
                        x=0.5,
                        font=dict(family='Vazirmatn', size=13)
                    ),
                    legend_font=dict(family='Vazirmatn'),
                    height=600,
                    margin=dict(l=60, r=40, t=80, b=120),
                    plot_bgcolor='#f8f9fa',
                    paper_bgcolor='white'
                )

                st.plotly_chart(fig_grouped, use_container_width=True, theme=None)

                # ─── Cumulative Flow: Waterfall Chart ───
                tot_dep = chart_data['adjusted_deposits'].sum()
                tot_pay = chart_data['adjusted_payments'].sum()
                tot_bal = chart_data['balance'].sum()

                waterfall_labels = [
                    ' واریزی تعدیل‌شده',
                    ' هزینه تعدیل‌شده',
                    ' مانده واقعی'
                ]
                waterfall_values = [tot_dep, -tot_pay, tot_bal]

                waterfall_max_value = max(tot_dep, tot_pay, abs(tot_bal), 0)
                waterfall_tickvals = [waterfall_max_value * i / 5 for i in range(6)] if waterfall_max_value > 0 else [0]
                waterfall_ticktext = [to_persian_numbers(int(v)) for v in waterfall_tickvals]

                fig_waterfall = go.Figure(go.Waterfall(
                    orientation='v',
                    measure=['relative', 'relative', 'total'],
                    x=waterfall_labels,
                    y=waterfall_values,
                    text=[to_persian_numbers(int(v)) for v in waterfall_values],
                    textposition='outside',
                    textfont=dict(family='Vazirmatn', size=12),
                    connector=dict(line=dict(color='#9CA3AF')),
                    increasing=dict(marker=dict(color='#10B981')),
                    decreasing=dict(marker=dict(color='#EF4444')),
                    totals=dict(marker=dict(color='#3B82F6'))
                ))

                fig_waterfall.update_layout(
                    font=dict(family='Vazirmatn', size=14),
                    title=dict(
                        text='نمای تجمعی جریان منابع و مصارف',
                        x=0.5,
                        xanchor='center',
                        font=dict(family='Vazirmatn', size=18)
                    ),
                    title_font=dict(family='Vazirmatn'),
                    xaxis=dict(
                        tickfont=dict(family='Vazirmatn', size=13),
                        title_font=dict(family='Vazirmatn')
                    ),
                    yaxis=dict(
                        title='مبلغ (میلیون ریال)',
                        tickmode='array',
                        tickvals=waterfall_tickvals,
                        ticktext=waterfall_ticktext,
                        tickfont=dict(family='Vazirmatn', size=12),
                        title_font=dict(family='Vazirmatn')
                    ),
                    showlegend=True,
                    legend=dict(
                        orientation='h',
                        yanchor='top',
                        y=-0.15,
                        xanchor='center',
                        x=0.5,
                        font=dict(family='Vazirmatn', size=13)
                    ),
                    height=520,
                    margin=dict(l=60, r=40, t=80, b=120),
                    plot_bgcolor='#f8f9fa',
                    paper_bgcolor='white'
                )

                st.plotly_chart(fig_waterfall, use_container_width=True, theme=None)

    finally:
        db.close()


if __name__ == "__main__":
    main()


## File: dashboard\CHANGELOG.md
------------------------------
# Dashboard Changelog

## Version 1.1 - Excel Export Feature

### Added
- **Excel Download Button**: Users can now export the annual financial breakdown table to Excel
- **`to_excel()` helper function**: Converts DataFrame to Excel format using BytesIO buffer
- **Dynamic filename**: Export files are named `financial_report_{employer_code}.xlsx` for easy identification

### Technical Details
- Import added: `io` from standard library
- Function signature: `to_excel(df) -> bytes`
- Uses `openpyxl` engine (already in requirements.txt)
- Button placed directly below the annual breakdown table
- Proper MIME type set for Excel downloads: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### User Experience
- Button label in Persian: "📥 دانلود گزارش به صورت اکسل"
- One-click download with no additional configuration needed
- Downloaded file preserves Persian column names and all formatting
- Numbers are exported in their numeric format (not comma-formatted strings) for further Excel calculations

### Code Changes
**File**: `dashboard/app.py`
- Line 3: Added `import io`
- Lines 140-144: New `to_excel()` helper function
- Lines 289-294: New `st.download_button` component

### Dependencies
No new dependencies required - `openpyxl` was already in requirements.txt

---

## Version 1.0 - Initial Release

### Features
- Employer selection dropdown
- Hierarchical support (Mother + Subsidiaries)
- Six KPI metrics
- Annual breakdown table
- Trend analysis chart
- Persian UI with RTL support


## File: dashboard\QUICKSTART.md
------------------------------
# راهنمای سریع اجرای داشبورد

## نصب وابستگی‌ها

اگر هنوز Streamlit را نصب نکرده‌اید:

```bash
pip install -r requirements.txt
```

## اجرای داشبورد

از دایرکتوری اصلی پروژه دستور زیر را اجرا کنید:

```bash
streamlit run dashboard/app.py
```

یا می‌توانید مستقیماً از پوشه dashboard اجرا کنید:

```bash
cd dashboard
streamlit run app.py
```

## دسترسی به داشبورد

پس از اجرا، داشبورد به صورت خودکار در مرورگر پیش‌فرض باز می‌شود:
- آدرس محلی: http://localhost:8501
- آدرس شبکه: http://YOUR_IP:8501

## توقف داشبورد

برای توقف سرور Streamlit، در ترمینال `Ctrl+C` را فشار دهید.

## عیب‌یابی

### خطای اتصال به دیتابیس
اطمینان حاصل کنید که:
1. فایل `.env` در دایرکتوری اصلی پروژه موجود است
2. متغیر `DATABASE_URL` به درستی تنظیم شده است
3. سرویس PostgreSQL در حال اجرا است

### خطای ماژول پیدا نشد
از دایرکتوری اصلی پروژه (همان جایی که `core/` و `models/` هستند) دستور را اجرا کنید.

### پورت در حال استفاده
اگر پورت 8501 در حال استفاده است:
```bash
streamlit run dashboard/app.py --server.port 8502
```

## گزینه‌های پیشرفته

### تغییر تم
```bash
streamlit run dashboard/app.py --theme.base "dark"
```

### اجرا بدون باز شدن مرورگر
```bash
streamlit run dashboard/app.py --server.headless true
```

### مشاهده لاگ‌ها
Streamlit به صورت خودکار لاگ‌ها را در ترمینال نمایش می‌دهد.


## File: dashboard\README.md
------------------------------
# داشبورد مدیریتی ساتع - ترازنامه مشمولین

## توضیحات
این داشبورد یک رابط کاربری تحت وب برای نمایش و تحلیل اطلاعات مالی مشمولین ساتع است. این برنامه با استفاده از Streamlit ساخته شده و اطلاعات را مستقیماً از پایگاه داده PostgreSQL می‌خواند.

## ویژگی‌های اصلی

### 1. انتخاب مشمول
- لیست کشویی شامل تمام مشمولین فعال
- نمایش نام و کد طبقه‌بندی

### 2. اطلاعات کلی مشمول
- نوع مشمول (Mother, Subsidiary, Independent)
- استان
- سازمان بالادست

### 3. KPI های مالی (خلاصه)
شش شاخص کلیدی برای کل دوره:
- **اعتبار تکلیفی**: مجموع اعتبارات تکلیفی تخصیص یافته
- **مجموع واریزی**: مجموع واریزهای انجام شده (شامل زیرمجموعه‌ها)
- **هزینه کرد**: مجموع پرداخت‌های انجام شده
- **انتقال ورودی**: مجموع انتقالات دریافتی
- **انتقال خروجی**: مجموع انتقالات ارسالی
- **مانده واقعی**: تراز نهایی محاسبه شده

### 4. جدول تفصیلی سالانه
نمایش اطلاعات مالی تفکیک شده به سال مالی با ستون‌های:
- سال مالی
- اعتبار تکلیفی
- مجموع واریزی
- هزینه کرد
- انتقال ورودی
- انتقال خروجی
- مانده واقعی (محاسبه شده)

### 5. نمودار تحلیلی
نمودار خطی نمایش روند:
- واریزی
- هزینه
- مانده

## فرمول محاسبه مانده
```
مانده واقعی = (مجموع واریزی + انتقال ورودی) - (هزینه کرد + انتقال خروجی)
```

## نحوه اجرا

### پیش‌نیازها
```bash
pip install -r requirements.txt
```

### اجرای داشبورد
```bash
streamlit run dashboard/app.py
```

پس از اجرا، داشبورد در مرورگر به صورت خودکار باز می‌شود (معمولاً در آدرس http://localhost:8501)

## نکات مهم

### پشتیبانی از ساختار سلسله‌مراتبی
- برای مشمولین از نوع **Mother**، داشبورد به صورت خودکار تمام زیرمجموعه‌ها را شناسایی کرده و در محاسبات لحاظ می‌کند
- این ویژگی از ستون `parent_code` در جدول `employers` استفاده می‌کند

### فیلتر حذف نرم (Soft Delete)
تمام کوئری‌ها فیلتر `is_deleted = False` را اعمال می‌کنند تا فقط رکوردهای فعال نمایش داده شوند.

### عملکرد
- استفاده از SQLAlchemy ORM برای کوئری‌های بهینه
- استفاده از Pandas برای پردازش و نمایش داده‌ها
- فرمت‌بندی اعداد با جداکننده هزارگان (comma-separated)

## ساختار کد

```
dashboard/
├── app.py              # فایل اصلی برنامه Streamlit
└── README.md           # این فایل
```

### توابع اصلی:

1. **get_active_employers()**: دریافت لیست مشمولین فعال
2. **get_employer_financials()**: جمع‌آوری و ترکیب اطلاعات مالی از جداول مختلف
3. **format_number()**: فرمت‌بندی اعداد برای نمایش
4. **main()**: تابع اصلی برنامه Streamlit

## منابع داده

داشبورد از جداول زیر استفاده می‌کند:
- `employers`: اطلاعات مشمولین
- `annual_mandates`: اعتبارات تکلیفی سالانه
- `deposit_receipts`: رسیدهای واریزی
- `contracts`: قراردادها
- `payments`: پرداخت‌ها
- `credit_transfers`: انتقالات اعتباری

## توسعه آینده

پیشنهادات برای نسخه‌های بعدی:
- اضافه کردن فیلتر محدوده زمانی
- نمایش جزئیات قراردادها و پژوهشگران
- امکان صادرات گزارش‌ها به Excel/PDF
- نمودارهای تعاملی با Plotly
- مقایسه چند مشمول همزمان
- داشبورد خلاصه برای تمام مشمولین

## پشتیبانی
برای گزارش مشکلات یا پیشنهادات، لطفاً با تیم توسعه تماس بگیرید.


## File: dashboard\views\batch_payments_page.py
------------------------------
"""Render the database-backed batch payment (draft/finalize) form.

Every draft is persisted to the ``payments`` table the moment it is added
(``POST /payments/draft``), so the list survives a browser reload. Funds
are reserved against the employer's real balance as soon as a draft is
created — the backend hard-blocks (HTTP 400) any payment that would take
the balance negative, superseding the old FR-18/19/20 warning-only rule.
"""

import io

import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/api/v1"

# Exact Persian headers/order required for both the on-screen drafts table
# and the finalized-batch Excel export.
DRAFT_TABLE_COLUMNS = [
    "کد رهگیری پرداخت",
    "کد قرارداد",
    "متقاضی",
    "دانشگاه یا موسسه مجری",
    "عنوان قرارداد",
    "مبلغ قرارداد (ریال)",
    "مبلغ پرداختی (ریال)",
    "پرداخت از محل سال مالی",
    "مانده متقاضی (ریال)",
]
NUMERIC_TABLE_COLUMNS = [
    "مبلغ قرارداد (ریال)",
    "مبلغ پرداختی (ریال)",
    "مانده متقاضی (ریال)",
]

# Widgets cleared after a successful "Add to Batch" — everything about the
# row just added, but not the global series/payment-year config.
ROW_RESET_KEYS = (
    "batch_search_query",
    "batch_contract_choice",
    "batch_pay_tracking_code",
    "batch_amount",
    "batch_funding_year",
)

FINALIZE_STATE_KEY = "batch_finalize_state"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox, p, div {
        direction: rtl !important;
        text-align: right !important;
    }
    [data-testid="stSidebarNav"] span {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.05rem !important;
    }
    h1 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; padding: 0 !important; }
    h2, h3 { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; padding: 0 !important; }
    hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
    .stBlock, .stVerticalBlock, [data-testid="stVerticalBlock"] > div {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
    }
    /* st.table renders a real HTML <table> (unlike st.dataframe, which draws
       cells on a <canvas> that ignores page CSS entirely — the root cause
       of the font/RTL/number-ordering bugs in the drafts table). */
    table, th, td, .stTable, [data-testid="stTable"] * {
        font-family: 'Vazirmatn', sans-serif !important;
        font-size: 15px !important;
        text-align: center !important;
        direction: rtl !important;
    }
    th { background-color: #f0f2f6 !important; border-bottom: 2px solid #4a4a4a !important; color: black !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📂 فرم ثبت دسته‌ای لیست پرداخت (کارتابل صندوق عتف)")


PERSIAN_DIGITS = {
    "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
    "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
}


def _to_persian_digits(text) -> str:
    """Convert ASCII digits to Persian digits.

    Western digits inside an RTL-directed comma-separated number are prone
    to bidi reordering in the browser (the exact "balance is messed up"
    symptom) — Persian digits are treated as part of the surrounding RTL
    run and render in the correct order, matching the convention already
    used for on-screen numbers elsewhere in this app (``dashboard/app.py``'s
    ``to_persian_numbers``).
    """
    text = str(text)
    for eng, per in PERSIAN_DIGITS.items():
        text = text.replace(eng, per)
    return text


def _format_rials(value) -> str:
    """Format a Rial amount with thousand separators in Persian digits, or '-' when absent."""
    if value is None:
        return "-"
    return _to_persian_digits(f"{value:,.0f}")


def _fetch_employer_balance(employer_code: str, funding_year: int) -> float | None:
    """Fetch an employer's current real balance for a funding year.

    Reflects every ``Draft``/``Final`` payment already on record (including
    drafts staged earlier in this same batch), so this is genuinely the
    balance "up to this moment" — not a stale snapshot.
    """
    try:
        response = requests.get(
            f"{API_URL}/employers/{employer_code}/balance",
            params={"funding_year": funding_year},
            timeout=5,
        )
        if response.status_code == 200:
            return response.json()["total_balance"]
        st.error(f"❌ خطا در دریافت موجودی کارفرما: {_response_detail(response)}")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت موجودی کارفرما: {exc}")
    return None


def _response_detail(response: requests.Response) -> str:
    """Extract a user-facing API error detail from JSON or text responses."""
    try:
        response_data = response.json()
    except ValueError:
        response_data = None

    if isinstance(response_data, dict):
        detail = response_data.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail
        if isinstance(detail, list):
            messages = [
                item.get("msg", str(item)) if isinstance(item, dict) else str(item)
                for item in detail
            ]
            return " ".join(messages)
    elif isinstance(response_data, str) and response_data.strip():
        return response_data

    return f"خطا در پردازش درخواست (کد وضعیت: {response.status_code})."


def _fetch_drafts(series: str) -> list[dict] | None:
    """Fetch active drafts for a series, handling connection errors gracefully."""
    try:
        response = requests.get(
            f"{API_URL}/payments/drafts", params={"series": series}, timeout=5
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"❌ خطا در دریافت لیست پیش‌نویس‌ها: {_response_detail(response)}")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت لیست پیش‌نویس‌ها: {exc}")
    return None


def _to_persian_row(item: dict) -> dict:
    """Map one enriched payment record onto the exact required headers."""
    return {
        "کد رهگیری پرداخت": item["tracking_code"],
        "کد قرارداد": item["contract_tracking_code"],
        "متقاضی": item.get("employer_name") or "-",
        "دانشگاه یا موسسه مجری": item.get("university_name") or "-",
        "عنوان قرارداد": item.get("contract_title") or "-",
        "مبلغ قرارداد (ریال)": item.get("contract_total_amount"),
        "مبلغ پرداختی (ریال)": item["amount"],
        "پرداخت از محل سال مالی": item["funding_year"],
        "مانده متقاضی (ریال)": item.get("employer_balance_after"),
    }


def _build_dataframe(items: list[dict]) -> pd.DataFrame:
    """Build the exact-header DataFrame shared by the table and the export."""
    rows = [_to_persian_row(item) for item in items]
    return pd.DataFrame(rows, columns=DRAFT_TABLE_COLUMNS)


def _display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Format numeric columns with Persian digits for on-screen display.

    Raw numbers stay in the Excel export (unaffected by this function).
    Tracking-code columns are deliberately left untouched — those are
    system identifiers, not display quantities, and must stay
    byte-for-byte matchable against the database.
    """
    display_df = df.copy()
    for column in NUMERIC_TABLE_COLUMNS:
        display_df[column] = display_df[column].apply(_format_rials)
    display_df["پرداخت از محل سال مالی"] = display_df["پرداخت از محل سال مالی"].apply(
        _to_persian_digits
    )
    return display_df


def _to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Convert the drafts/finalized DataFrame to an in-memory Excel file."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Payments")
    output.seek(0)
    return output.getvalue()


def _apply_pending_row_reset() -> None:
    """Clear the just-added row's widget state before the widgets are recreated."""
    if not st.session_state.pop("batch_row_reset_pending", False):
        return
    for widget_key in ROW_RESET_KEYS:
        st.session_state.pop(widget_key, None)


def _schedule_row_reset() -> None:
    st.session_state.batch_row_reset_pending = True
    st.rerun()


_apply_pending_row_reset()

# st.success() is an ephemeral inline element cleared by an immediately
# following st.rerun() — unlike st.toast(), it does not survive into the
# next run. Both the "row added" balance message and the finalize message
# are therefore stashed in session_state and rendered once, here, right
# after the rerun that follows a successful action.
add_success_message = st.session_state.pop("batch_add_success_message", None)
if add_success_message:
    st.success(add_success_message)

finalize_success_message = st.session_state.pop("batch_finalize_success_message", None)
if finalize_success_message:
    st.success(finalize_success_message)


# ─── Finalized "success state": Excel download, entry UI hidden ──────────
finalize_state = st.session_state.get(FINALIZE_STATE_KEY)
if finalize_state:
    st.download_button(
        label="📥 دانلود فایل اکسل لیست پرداخت",
        data=finalize_state["excel_bytes"],
        file_name=finalize_state["filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
    st.markdown("---")
    st.table(_display_dataframe(finalize_state["dataframe"]).reset_index(drop=True))
    if st.button("🆕 شروع لیست پرداخت جدید"):
        st.session_state.pop(FINALIZE_STATE_KEY, None)
        st.rerun()
    st.stop()


# ─── 1. Global Config: applies to every new row added below ──────────────
st.subheader("۱. اطلاعات کلی لیست پرداخت")
col_s1, col_s2 = st.columns(2)
with col_s1:
    series_number = st.text_input(
        "شماره سری پرداخت (لیست):", value="15", key="batch_series"
    )
with col_s2:
    payment_year = st.number_input(
        "سال پرداخت (شمسی):",
        min_value=1398,
        max_value=1410,
        value=1405,
        key="batch_payment_year",
    )

st.markdown("---")

# ─── 2. Add New Row: search a contract, then stage a draft against it ────
st.subheader("۲. ورود اطلاعات ردیف جدید")

search_query = st.text_input(
    "🔍 جستجوی قرارداد (کد رهگیری یا بخشی از عنوان قرارداد):",
    key="batch_search_query",
)
selected_contract = None

if search_query:
    try:
        response = requests.get(
            f"{API_URL}/contracts/search", params={"q": search_query}, timeout=5
        )
        if response.status_code == 200 and response.json():
            contracts_found = response.json()
            options = {
                f"{c['contract_tracking_code']} - {c['title'][:40]}...": c
                for c in contracts_found
            }
            choice = st.selectbox(
                "قرارداد مورد نظر را انتخاب کنید:",
                list(options.keys()),
                key="batch_contract_choice",
            )
            selected_contract = options[choice]
            st.success(
                f"🏢 متقاضی (شرکت مادر): {selected_contract['employer_name']} | "
                f"🎓 مجری: {selected_contract['university_name']} | "
                f"🧑‍💻 فناور: {selected_contract['researcher_name']}"
            )

            # Live balance preview: the funding-year widget below hasn't run
            # yet this script pass, so its *previous* value (or the default,
            # on first selection) is read straight from session_state — the
            # same value that widget is about to render with.
            preview_funding_year = st.session_state.get("batch_funding_year", 1402)
            preview_balance = _fetch_employer_balance(
                selected_contract["employer_classification_code"], preview_funding_year
            )
            if preview_balance is not None:
                st.info(
                    f"💰 موجودی فعلی کارفرما تا این لحظه (سال مالی "
                    f"{_to_persian_digits(preview_funding_year)}): "
                    f"{_format_rials(preview_balance)} ریال"
                )
        else:
            st.warning("هیچ قراردادی با این مشخصات یافت نشد.")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطا در اتصال به بک‌اند: {exc}")

col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    pay_tracking_code = st.text_input(
        "کد رهگیری پرداخت (از سامانه ساتع):", key="batch_pay_tracking_code"
    )
with col_r2:
    # Integer-only amount: value/step are ints, which puts st.number_input
    # into integer mode (it returns a float if any of value/step/min/max
    # were floats), and format="%d" keeps the on-screen display integral.
    amount = st.number_input(
        "مبلغ پرداختی (ریال):",
        min_value=0,
        step=1000000,
        format="%d",
        value=0,
        key="batch_amount",
    )
with col_r3:
    funding_year = st.number_input(
        "پرداخت از محل سال مالی (شمسی):",
        min_value=1398,
        max_value=1410,
        value=1402,
        key="batch_funding_year",
    )

if st.button("➕ افزودن به لیست", type="primary"):
    if not selected_contract or not pay_tracking_code.strip() or amount <= 0:
        st.error("لطفاً تمامی فیلدهای الزامی ردیف را تکمیل کنید.")
    elif not series_number.strip():
        st.error("لطفاً شماره سری پرداخت را وارد کنید.")
    else:
        draft_payload = {
            "tracking_code": pay_tracking_code.strip(),
            "contract_tracking_code": selected_contract["contract_tracking_code"],
            "amount": int(amount),
            "funding_year": int(funding_year),
            "payment_year": int(payment_year),
            "series": series_number.strip(),
        }
        try:
            draft_response = requests.post(
                f"{API_URL}/payments/draft", json=draft_payload, timeout=10
            )
            if draft_response.status_code == 201:
                data = draft_response.json()
                st.session_state.batch_add_success_message = (
                    "✅ پرداخت به لیست اضافه شد. "
                    f"مانده کارفرما قبل از پرداخت: {_format_rials(data['employer_balance_before'])} ریال "
                    f"| مانده پس از پرداخت: {_format_rials(data['employer_balance_after'])} ریال"
                )
                _schedule_row_reset()
            elif draft_response.status_code == 400:
                # Insufficient funds or duplicate tracking code — the exact
                # backend message (deficit amount, etc.) is shown verbatim.
                st.error(f"❌ {_response_detail(draft_response)}")
            else:
                st.error(f"❌ خطا در افزودن ردیف: {_response_detail(draft_response)}")
        except requests.exceptions.ConnectionError:
            st.error(
                "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
                "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
            )
        except requests.exceptions.Timeout:
            st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
        except Exception as exc:
            st.error(f"خطا در ارتباط با سرور: {exc}")

st.markdown("---")

# ─── 3. Data Table: always reflects the database, not local state ────────
st.subheader("۳. لیست پیش‌نویس پرداخت‌های در حال انتظار (ثبت‌شده در پایگاه داده)")

current_series = series_number.strip()
drafts = _fetch_drafts(current_series) if current_series else None

if drafts:
    drafts_df = _build_dataframe(drafts)
    st.table(_display_dataframe(drafts_df).reset_index(drop=True))

    delete_col1, delete_col2 = st.columns([3, 1])
    with delete_col1:
        delete_options = {
            f"{d['tracking_code']} — {d.get('employer_name') or '-'} "
            f"({_format_rials(d['amount'])} ریال)": d["tracking_code"]
            for d in drafts
        }
        delete_choice = st.selectbox(
            "حذف یک ردیف از لیست:", list(delete_options.keys()), key="batch_delete_choice"
        )
    with delete_col2:
        st.write("")
        st.write("")
        if st.button("🗑️ حذف ردیف انتخاب‌شده"):
            tracking_code_to_delete = delete_options[delete_choice]
            try:
                delete_response = requests.delete(
                    f"{API_URL}/payments/draft/{tracking_code_to_delete}", timeout=10
                )
                if delete_response.status_code == 200:
                    st.toast("🗑️ ردیف حذف شد.", icon="🗑️")
                    st.rerun()
                else:
                    st.error(f"❌ خطا در حذف ردیف: {_response_detail(delete_response)}")
            except requests.exceptions.ConnectionError:
                st.error(
                    "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
                    "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
                )
            except Exception as exc:
                st.error(f"خطا در حذف ردیف: {exc}")

    st.markdown("### 🚀 نهایی‌سازی و ثبت در دیتابیس")
    if st.button("💾 تأیید نهایی لیست", type="primary"):
        try:
            finalize_response = requests.post(
                f"{API_URL}/payments/finalize-batch",
                json={"series": current_series},
                timeout=10,
            )
            if finalize_response.status_code == 200:
                data = finalize_response.json()
                finalized_df = _build_dataframe(data["finalized_payments"])
                st.session_state[FINALIZE_STATE_KEY] = {
                    "excel_bytes": _to_excel_bytes(finalized_df),
                    "filename": f"payments_series_{current_series}.xlsx",
                    "dataframe": finalized_df,
                }
                st.session_state.batch_finalize_success_message = (
                    f"🎉 لیست با موفقیت نهایی شد! {data['finalized_count']} "
                    "قلم پرداخت ثبت و قفل گردید."
                )
                st.rerun()
            else:
                st.error(f"❌ خطا در نهایی‌سازی: {_response_detail(finalize_response)}")
        except requests.exceptions.ConnectionError:
            st.error(
                "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
                "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
            )
        except Exception as exc:
            st.error(f"خطا در ارسال نهایی به سرور: {exc}")
elif drafts is not None:
    st.info(
        "لیست پیش‌نویس برای این سری در حال حاضر خالی است. "
        "ردیف‌های پرداخت را از بخش بالا اضافه کنید."
    )


## File: dashboard\views\contract_edit_page.py
------------------------------
"""Render the contract search-and-edit form (Phase 4 follow-up)."""

from datetime import date

import jdatetime
import requests
import streamlit as st

from core.date_helper import parse_strict_jalali_iso

API_URL = "http://127.0.0.1:8000/api/v1"
SELECTED_TRACKING_CODE_KEY = "contract_edit_selected_tracking_code"
LOADED_DETAIL_KEY = "contract_edit_loaded_detail"
LOAD_SEQ_KEY = "contract_edit_load_seq"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox,
    .stDateInput, p, div {
        direction: rtl !important;
        text-align: right !important;
    }
    [data-testid="stSidebarNav"] span {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.05rem !important;
    }
    div[data-testid="InputInstructions"] { display: none !important; }
    h1 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; padding: 0 !important; }
    h2, h3 { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; padding: 0 !important; }
    hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("✏️ جستجو و ویرایش قرارداد")


def _safe_lookup(path: str) -> list[dict]:
    """Fetch a lookup list and display a localized error when unavailable."""
    try:
        response = requests.get(f"{API_URL}{path}", timeout=5)
        if response.status_code == 200:
            return response.json()
        st.error(f"خطا در دریافت اطلاعات ({path}): {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت اطلاعات: {exc}")
    return []


def _format_option(item: dict, value_key: str) -> str:
    """Format lookup entries as a human-readable code and name pair."""
    return f"{item[value_key]} - {item['name']}"


def _optional_text(value: str) -> str | None:
    """Return stripped optional form text or ``None`` when empty."""
    normalized_value = value.strip()
    return normalized_value or None


def _response_detail(response: requests.Response) -> str:
    """Extract a user-facing API error detail from JSON or text responses."""
    try:
        response_data = response.json()
    except ValueError:
        response_data = None

    if isinstance(response_data, dict):
        detail = response_data.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail
        if isinstance(detail, list):
            messages = [
                item.get("msg", str(item)) if isinstance(item, dict) else str(item)
                for item in detail
            ]
            return " ".join(messages)
    elif isinstance(response_data, str) and response_data.strip():
        return response_data

    return f"خطا در پردازش درخواست (کد وضعیت: {response.status_code})."


def _fetch_contract_detail(tracking_code: str) -> dict | None:
    """Fetch full contract details for editing, handling errors gracefully."""
    try:
        response = requests.get(
            f"{API_URL}/contracts/{tracking_code}", timeout=5
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"❌ خطا در دریافت اطلاعات قرارداد: {_response_detail(response)}")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت اطلاعات قرارداد: {exc}")
    return None


def _gregorian_iso_to_jalali_str(iso_date: str | None) -> str:
    """Convert a Gregorian ISO date string to a Jalali ``YYYY/MM/DD`` string."""
    if not iso_date:
        return ""
    gregorian_date = date.fromisoformat(iso_date)
    return jdatetime.date.fromgregorian(date=gregorian_date).strftime("%Y/%m/%d")


def _index_of(options: list[str], current_value: str | None) -> int:
    """Return the dropdown index for the contract's current FK value.

    Falls back to ``0`` (and a warning) if the stored value is somehow
    absent from the active lookup — e.g. the linked record was soft-deleted
    after the contract was created.
    """
    if current_value in options:
        return options.index(current_value)
    return 0


employers = _safe_lookup("/employers/lookup")
universities = _safe_lookup("/universities/lookup")
researchers = _safe_lookup("/researchers/lookup")

if not employers or not universities or not researchers:
    st.warning(
        "برای ادامه، ابتدا باید حداقل یک کارفرما (غیر زیرمجموعه)، "
        "یک دانشگاه و یک فناور در سیستم موجود باشد."
    )
    st.stop()

employer_options = {
    item["classification_code"]: _format_option(item, "classification_code")
    for item in employers
}
university_options = {
    item["national_id"]: _format_option(item, "national_id")
    for item in universities
}
researcher_options = {
    item["national_id"]: _format_option(item, "national_id")
    for item in researchers
}

success_message = st.session_state.pop("contract_edit_success_message", None)
if success_message:
    st.success(success_message)
    st.toast("✅ قرارداد با موفقیت ویرایش شد.", icon="✏️")

# ─── 1. Search ───────────────────────────────────────────────────────────
st.subheader("۱. جستجوی قرارداد")
search_query = st.text_input(
    "🔍 جستجو بر اساس کد رهگیری یا عنوان قرارداد:",
    key="contract_edit_search_query",
)

selected_contract = None
if search_query:
    try:
        response = requests.get(
            f"{API_URL}/contracts/search", params={"q": search_query}, timeout=5
        )
        if response.status_code == 200 and response.json():
            contracts_found = response.json()
            options = {
                f"{c['contract_tracking_code']} - {c['title'][:40]}": c
                for c in contracts_found
            }
            choice = st.selectbox(
                "قرارداد مورد نظر برای ویرایش را انتخاب کنید:",
                list(options.keys()),
                key="contract_edit_search_choice",
            )
            selected_contract = options[choice]
        else:
            st.warning("هیچ قراردادی با این مشخصات یافت نشد.")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطا در جستجوی قرارداد: {exc}")

# ─── 2. Load full details once a contract is selected ───────────────────
if selected_contract is not None:
    tracking_code = selected_contract["contract_tracking_code"]
    if st.session_state.get(SELECTED_TRACKING_CODE_KEY) != tracking_code:
        detail = _fetch_contract_detail(tracking_code)
        if detail is not None:
            st.session_state[SELECTED_TRACKING_CODE_KEY] = tracking_code
            st.session_state[LOADED_DETAIL_KEY] = detail
            # Bump the load sequence so widget keys below are unique per
            # fetch, not just per tracking_code. Without this, re-editing
            # the *same* contract again later in one browser session would
            # reuse Streamlit's cached widget state from the previous edit
            # instead of the freshly fetched values, since a widget's
            # `value=`/`index=` argument is ignored once its key already
            # has an entry in session_state.
            st.session_state[LOAD_SEQ_KEY] = (
                st.session_state.get(LOAD_SEQ_KEY, 0) + 1
            )

detail = st.session_state.get(LOADED_DETAIL_KEY)

# ─── 3. Pre-filled edit form ─────────────────────────────────────────────
if detail is not None:
    tracking_code = detail["tracking_code"]
    form_instance_key = f"{tracking_code}_{st.session_state.get(LOAD_SEQ_KEY, 0)}"
    st.markdown("---")
    st.subheader(f"۲. ویرایش قرارداد: {tracking_code}")

    # Widget keys are namespaced per (tracking_code, load sequence) so both
    # switching to a different contract AND reloading the same contract
    # again create fresh widgets pre-filled with the newly loaded values.
    with st.form(f"contract_edit_form_{form_instance_key}", clear_on_submit=False):
        st.markdown("**۱. اطلاعات طرف‌های قرارداد**")
        employer_keys = list(employer_options)
        university_keys = list(university_options)
        researcher_keys = list(researcher_options)

        employer_choice = st.selectbox(
            "🏢 کارفرما (شرکت مادر):",
            options=employer_keys,
            format_func=employer_options.get,
            index=_index_of(
                employer_keys, detail["employer_classification_code"]
            ),
            key=f"edit_employer_{form_instance_key}",
        )
        university_choice = st.selectbox(
            "🎓 مجری (دانشگاه/موسسه):",
            options=university_keys,
            format_func=university_options.get,
            index=_index_of(
                university_keys, detail["university_national_id"]
            ),
            key=f"edit_university_{form_instance_key}",
        )
        researcher_choice = st.selectbox(
            "🧑‍💻 فناور (مجری پروژه):",
            options=researcher_keys,
            format_func=researcher_options.get,
            index=_index_of(
                researcher_keys, detail["researcher_national_id"]
            ),
            key=f"edit_researcher_{form_instance_key}",
        )

        st.markdown("---")
        st.markdown("**۲. مشخصات قرارداد**")

        identifier_col, proposal_col = st.columns(2)
        with identifier_col:
            contract_number = st.text_input(
                "📑 شماره قرارداد:",
                value=detail.get("contract_number") or "",
                key=f"edit_contract_number_{form_instance_key}",
            )
        with proposal_col:
            proposal_id = st.text_input(
                "🧾 شناسه پیشنهاده:",
                value=detail.get("proposal_id") or "",
                key=f"edit_proposal_id_{form_instance_key}",
            )

        title = st.text_input(
            "📝 عنوان قرارداد:",
            value=detail["title"],
            key=f"edit_title_{form_instance_key}",
        )

        amount_col, duration_col = st.columns(2)
        with amount_col:
            total_amount = st.number_input(
                "💰 مبلغ کل قرارداد (ریال):",
                min_value=0.0,
                step=1_000_000.0,
                format="%.2f",
                value=float(detail["total_amount"]),
                key=f"edit_total_amount_{form_instance_key}",
            )
        with duration_col:
            duration_months = st.number_input(
                "⏳ مدت قرارداد (ماه):",
                min_value=1,
                step=1,
                value=int(detail.get("duration_months") or 1),
                key=f"edit_duration_months_{form_instance_key}",
            )

        contract_date_str = st.text_input(
            "📅 تاریخ انعقاد قرارداد (شمسی):",
            value=_gregorian_iso_to_jalali_str(detail.get("contract_date")),
            placeholder="مثال: 1403/05/12",
            key=f"edit_contract_date_{form_instance_key}",
        )

        if detail.get("attachment_path"):
            st.caption(f"📎 فایل پیوست فعلی: {detail['attachment_path']}")
        else:
            st.caption("📎 هیچ فایل پیوستی برای این قرارداد ثبت نشده است.")

        submitted = st.form_submit_button("💾 ذخیره تغییرات", type="primary")

    if submitted:
        if not title.strip():
            st.error("لطفاً عنوان قرارداد را تکمیل کنید.")
        elif total_amount <= 0:
            st.error("مبلغ قرارداد باید بیشتر از صفر باشد.")
        else:
            try:
                contract_date_iso = parse_strict_jalali_iso(contract_date_str)
            except ValueError:
                st.warning(
                    "تاریخ نامعتبر است. بررسی کنید که روز و ماه با تقویم شمسی "
                    "تطابق داشته باشد."
                )
            else:
                payload = {
                    "employer_classification_code": employer_choice,
                    "university_national_id": university_choice,
                    "researcher_national_id": researcher_choice,
                    "contract_number": _optional_text(contract_number),
                    "proposal_id": _optional_text(proposal_id),
                    "attachment_path": detail.get("attachment_path"),
                    "title": title.strip(),
                    "total_amount": int(total_amount),
                    "contract_date": contract_date_iso,
                    "duration_months": int(duration_months),
                }
                try:
                    response = requests.put(
                        f"{API_URL}/contracts/{tracking_code}",
                        json=payload,
                        timeout=10,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.contract_edit_success_message = (
                            "🎉 قرارداد با موفقیت ویرایش شد. "
                            f"کد: {data.get('contract_tracking_code')} | "
                            f"کارفرما: {data.get('employer_name')} | "
                            f"دانشگاه: {data.get('university_name')} | "
                            f"فناور: {data.get('researcher_name')}"
                        )
                        # Clear loaded state so the page returns to search.
                        st.session_state.pop(SELECTED_TRACKING_CODE_KEY, None)
                        st.session_state.pop(LOADED_DETAIL_KEY, None)
                        st.rerun()
                    else:
                        st.error(
                            f"❌ خطا در ذخیره تغییرات: {_response_detail(response)}"
                        )
                except requests.exceptions.ConnectionError:
                    st.error(
                        "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن "
                        "شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
                    )
                except requests.exceptions.Timeout:
                    st.error(
                        "خطا: پاسخ سرور بیش از حد طول کشید. لطفاً مجدداً تلاش کنید."
                    )
                except Exception as exc:
                    st.error(f"خطا در ارسال اطلاعات به سرور: {exc}")
elif search_query and selected_contract is None:
    st.info("قراردادی را از نتایج جستجو انتخاب کنید تا فرم ویرایش نمایش داده شود.")


## File: dashboard\views\contract_entry_page.py
------------------------------
"""Render the Phase 4 contract registration form."""

import re
from pathlib import Path
from uuid import uuid4

import requests
import streamlit as st

from core.date_helper import parse_strict_jalali_iso

API_URL = "http://127.0.0.1:8000/api/v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ARCHIVE_DIR = PROJECT_ROOT / "data" / "Archive" / "Contracts"
ALLOWED_ATTACHMENT_TYPES = {"pdf", "jpg", "jpeg", "png"}
FORM_KEY = "contract_entry_form"
FORM_WIDGET_KEYS = (
    "contract_employer",
    "contract_university",
    "contract_researcher",
    "contract_tracking_code",
    "contract_number",
    "contract_proposal_id",
    "contract_title",
    "contract_total_amount",
    "contract_duration_months",
    "contract_date",
    "contract_attachment",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
    * { font-family: 'Vazirmatn', sans-serif !important; }
    .block-container, .stTextInput, .stNumberInput, .stSelectbox,
    .stDateInput, .stFileUploader, p, div {
        direction: rtl !important;
        text-align: right !important;
    }
    [data-testid="stSidebarNav"] span {
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.05rem !important;
    }
    div[data-testid="InputInstructions"] { display: none !important; }
    h1 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; padding: 0 !important; }
    h2, h3 { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; padding: 0 !important; }
    hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📄 فرم ثبت قرارداد جدید")


def _safe_lookup(path: str) -> list[dict]:
    """Fetch a lookup list and display a localized error when unavailable."""
    try:
        response = requests.get(f"{API_URL}{path}", timeout=5)
        if response.status_code == 200:
            return response.json()
        st.error(f"خطا در دریافت اطلاعات ({path}): {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error(
            "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
            "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
        )
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as exc:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت اطلاعات: {exc}")
    return []


def _format_option(item: dict, value_key: str) -> str:
    """Format lookup entries as a human-readable code and name pair."""
    return f"{item[value_key]} - {item['name']}"


def _optional_text(value: str) -> str | None:
    """Return stripped optional form text or ``None`` when empty."""
    normalized_value = value.strip()
    return normalized_value or None


def _safe_filename(original_name: str) -> str:
    """Create a collision-resistant filename without unsafe path characters."""
    original_path = Path(original_name)
    extension = original_path.suffix.lower()
    sanitized_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", original_path.stem).strip("_")
    safe_stem = sanitized_stem[:80] or "contract"
    return f"{safe_stem}_{uuid4().hex}{extension}"


def _save_attachment(uploaded_file) -> Path | None:
    """Save an uploaded contract document and return its project-relative path."""
    if uploaded_file is None:
        return None

    extension = Path(uploaded_file.name).suffix.lower().lstrip(".")
    if extension not in ALLOWED_ATTACHMENT_TYPES:
        raise ValueError("نوع فایل نامعتبر است. فقط PDF، JPG و PNG مجاز هستند.")

    CONTRACT_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    destination = CONTRACT_ARCHIVE_DIR / _safe_filename(uploaded_file.name)
    destination.write_bytes(uploaded_file.getvalue())
    return destination.relative_to(PROJECT_ROOT)


def _delete_attachment(relative_path: Path | None) -> None:
    """Remove a newly saved attachment after a failed contract submission."""
    if relative_path is None:
        return
    absolute_path = (PROJECT_ROOT / relative_path).resolve()
    archive_root = CONTRACT_ARCHIVE_DIR.resolve()
    if archive_root not in absolute_path.parents:
        return
    absolute_path.unlink(missing_ok=True)


def _schedule_form_reset() -> None:
    """Schedule widget cleanup for the next Streamlit render cycle."""
    st.session_state.contract_form_reset_pending = True
    st.rerun()


def _apply_pending_form_reset() -> None:
    """Clear contract widget state before the widgets are recreated."""
    if not st.session_state.pop("contract_form_reset_pending", False):
        return
    for widget_key in FORM_WIDGET_KEYS:
        st.session_state.pop(widget_key, None)


def _response_detail(response: requests.Response) -> str:
    """Extract a user-facing API error detail from JSON or text responses."""
    try:
        response_data = response.json()
    except ValueError:
        response_data = None

    if isinstance(response_data, dict):
        detail = response_data.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail
        if isinstance(detail, list):
            messages = [
                item.get("msg", str(item)) if isinstance(item, dict) else str(item)
                for item in detail
            ]
            return " ".join(messages)
    elif isinstance(response_data, str) and response_data.strip():
        return response_data

    return f"خطا در ثبت قرارداد (کد وضعیت: {response.status_code})."


_apply_pending_form_reset()

employers = _safe_lookup("/employers/lookup")
universities = _safe_lookup("/universities/lookup")
researchers = _safe_lookup("/researchers/lookup")

if not employers or not universities or not researchers:
    st.warning(
        "برای ادامه، ابتدا باید حداقل یک کارفرما (غیر زیرمجموعه)، "
        "یک دانشگاه و یک فناور در سیستم موجود باشد."
    )
    st.stop()

success_message = st.session_state.pop("contract_success_message", None)
if success_message:
    st.success(success_message)
    st.toast("✅ قرارداد جدید ثبت شد.", icon="📄")

employer_options = {
    item["classification_code"]: _format_option(item, "classification_code")
    for item in employers
}
university_options = {
    item["national_id"]: _format_option(item, "national_id")
    for item in universities
}
researcher_options = {
    item["national_id"]: _format_option(item, "national_id")
    for item in researchers
}

with st.form(FORM_KEY, clear_on_submit=False):
    st.subheader("۱. اطلاعات طرف‌های قرارداد")
    employer_choice = st.selectbox(
        "🏢 کارفرما (شرکت مادر):",
        options=list(employer_options),
        format_func=employer_options.get,
        key="contract_employer",
    )
    university_choice = st.selectbox(
        "🎓 مجری (دانشگاه/موسسه):",
        options=list(university_options),
        format_func=university_options.get,
        key="contract_university",
    )
    researcher_choice = st.selectbox(
        "🧑‍💻 فناور (مجری پروژه):",
        options=list(researcher_options),
        format_func=researcher_options.get,
        key="contract_researcher",
    )

    st.markdown("---")
    st.subheader("۲. مشخصات قرارداد")
    tracking_code = st.text_input(
        "🔖 کد رهگیری قرارداد:", key="contract_tracking_code"
    )

    identifier_col, proposal_col = st.columns(2)
    with identifier_col:
        contract_number = st.text_input(
            "📑 شماره قرارداد:", key="contract_number"
        )
    with proposal_col:
        proposal_id = st.text_input(
            "🧾 شناسه پیشنهاده:", key="contract_proposal_id"
        )

    title = st.text_input("📝 عنوان قرارداد:", key="contract_title")
    amount_col, duration_col = st.columns(2)
    with amount_col:
        total_amount = st.number_input(
            "💰 مبلغ کل قرارداد (ریال):",
            min_value=0.0,
            step=1_000_000.0,
            format="%.2f",
            key="contract_total_amount",
        )
    with duration_col:
        duration_months = st.number_input(
            "⏳ مدت قرارداد (ماه):",
            min_value=1,
            step=1,
            value=12,
            key="contract_duration_months",
        )

    contract_date_str = st.text_input(
        "📅 تاریخ انعقاد قرارداد (شمسی):",
        placeholder="مثال: 1403/05/12",
        key="contract_date",
    )
    attachment = st.file_uploader(
        "📎 فایل قرارداد (PDF/JPG/PNG):",
        type=sorted(ALLOWED_ATTACHMENT_TYPES),
        key="contract_attachment",
    )
    submitted = st.form_submit_button("✅ ثبت قرارداد", type="primary")

if submitted:
    if not tracking_code.strip() or not title.strip():
        st.error("لطفاً کد رهگیری و عنوان قرارداد را تکمیل کنید.")
    elif total_amount <= 0:
        st.error("مبلغ قرارداد باید بیشتر از صفر باشد.")
    else:
        try:
            contract_date_iso = parse_strict_jalali_iso(contract_date_str)
        except ValueError:
            st.warning(
                "تاریخ نامعتبر است. بررسی کنید که روز و ماه با تقویم شمسی "
                "تطابق داشته باشد."
            )
        else:
            attachment_path = None
            try:
                attachment_path = _save_attachment(attachment)
                payload = {
                    "tracking_code": tracking_code.strip(),
                    "employer_classification_code": employer_choice,
                    "university_national_id": university_choice,
                    "researcher_national_id": researcher_choice,
                    "contract_number": _optional_text(contract_number),
                    "proposal_id": _optional_text(proposal_id),
                    "attachment_path": (
                        attachment_path.as_posix() if attachment_path else None
                    ),
                    "title": title.strip(),
                    "total_amount": float(total_amount),
                    "contract_date": contract_date_iso,
                    "duration_months": int(duration_months),
                }
                response = requests.post(
                    f"{API_URL}/contracts/", json=payload, timeout=10
                )
                if response.status_code == 201:
                    data = response.json()
                    st.session_state.contract_success_message = (
                        "🎉 قرارداد با موفقیت ثبت شد. "
                        f"کد: {data.get('contract_tracking_code')} | "
                        f"کارفرما: {data.get('employer_name')} | "
                        f"دانشگاه: {data.get('university_name')} | "
                        f"فناور: {data.get('researcher_name')}"
                    )
                    _schedule_form_reset()
                else:
                    _delete_attachment(attachment_path)
                    st.error(f"❌ خطا در ثبت قرارداد: {_response_detail(response)}")
            except ValueError as exc:
                _delete_attachment(attachment_path)
                st.error(str(exc))
            except requests.exceptions.ConnectionError:
                _delete_attachment(attachment_path)
                st.error(
                    "خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید "
                    "سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است."
                )
            except requests.exceptions.Timeout:
                _delete_attachment(attachment_path)
                st.error("خطا: پاسخ سرور بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
            except OSError as exc:
                _delete_attachment(attachment_path)
                st.error(f"خطا در ذخیره فایل قرارداد: {exc}")
            except Exception as exc:
                _delete_attachment(attachment_path)
                st.error(f"خطا در ارسال اطلاعات به سرور: {exc}")


## File: dashboard\views\researcher_entry_page.py
------------------------------
# File: views/researcher_entry_page.py
"""Phase 4 - New Researcher (فناور) registration form."""
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api/v1"

# ─── Aggressive RTL override + compact Persian theme ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
* { font-family: 'Vazirmatn', sans-serif !important; }
.block-container, .stTextInput, .stNumberInput, .stSelectbox, .stCheckbox, p, div {
    direction: rtl !important;
    text-align: right !important;
}
[data-testid="stSidebarNav"] span {
    direction: rtl !important;
    text-align: right !important;
    font-size: 1.05rem !important;
}
h1 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; padding: 0 !important; }
h2, h3 { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; padding: 0 !important; }
hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("🧑‍🔬 فرم ثبت اطلاعات فناور")


def _fetch_universities():
    """Fetch universities for the dropdown; returns list or [] with friendly error."""
    try:
        resp = requests.get(f"{API_URL}/universities/lookup", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        st.error(f"خطا در دریافت لیست موسسات: {resp.status_code}")
        return []
    except requests.exceptions.ConnectionError:
        st.error("خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است.")
        return []
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
        return []
    except Exception as e:
        st.error(f"خطای پیش‌بینی‌نشده در دریافت موسسات: {e}")
        return []


fetched_universities = _fetch_universities()
# Smart mapping: display names in the UI, resolve to national_id on submit.
university_map = {u["name"]: u["national_id"] for u in fetched_universities}

ACADEMIC_RANKS = ["استاد", "دانشیار", "استادیار", "مربی", "پژوهشگر", "سایر"]
EDUCATION_LEVELS = ["دکتری", "کارشناسی ارشد", "کارشناسی", "سایر"]
RESEARCHER_TYPES = ["هیات علمی", "پژوهشگر آزاد", "دانشجو", "سایر"]
STATUS_OPTIONS = {"فعال": "Active", "غیرفعال": "Inactive"}

with st.form("researcher_entry_form", clear_on_submit=False):
    st.subheader("۱. اطلاعات هویتی")

    national_code = st.text_input("🪪 کد ملی فناور:", placeholder="۱۰ رقم", max_chars=10)

    col_first, col_last = st.columns(2)
    with col_first:
        first_name = st.text_input("👤 نام:")
    with col_last:
        last_name = st.text_input("👥 نام خانوادگی:")

    col_mobile, col_email = st.columns(2)
    with col_mobile:
        mobile = st.text_input("📱 تلفن همراه (اختیاری):", placeholder="مثال: 09123456789")
    with col_email:
        email = st.text_input("✉️ ایمیل (اختیاری):", placeholder="example@mail.com")

    st.markdown("---")
    st.subheader("۲. اطلاعات علمی و وابستگی سازمانی")

    if university_map:
        university_name = st.selectbox("🏫 موسسه محل فعالیت:", options=list(university_map.keys()))
    else:
        st.warning("هیچ موسسه‌ای برای انتخاب یافت نشد. ابتدا یک موسسه ثبت کنید.")
        university_name = None

    col_rank, col_edu = st.columns(2)
    with col_rank:
        academic_rank = st.selectbox("🎓 مرتبه علمی:", options=ACADEMIC_RANKS)
    with col_edu:
        education_level = st.selectbox("🎓 سطح تحصیلات:", options=EDUCATION_LEVELS)

    researcher_type = st.selectbox("🏷️ نوع فناور:", options=RESEARCHER_TYPES)
    status_label = st.selectbox("🟢 وضعیت:", options=list(STATUS_OPTIONS.keys()), index=0)

    submitted = st.form_submit_button("✅ ثبت فناور", type="primary")

    if submitted:
        if university_name is None:
            st.error("موسسه محل فعالیت قابل انتخاب نیست.")
        elif not national_code.strip() or len(national_code.strip()) != 10 or not national_code.strip().isdigit():
            st.error("کد ملی باید دقیقاً ۱۰ رقم باشد.")
        elif not first_name.strip() or not last_name.strip():
            st.error("لطفاً نام و نام خانوادگی را وارد کنید.")
        else:
            payload = {
                "national_code": national_code.strip(),
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "mobile": mobile.strip() or None,
                "email": email.strip() or None,
                "academic_rank": academic_rank,
                "education_level": education_level,
                "researcher_type": researcher_type,
                "university_id": university_map[university_name],
                "status": STATUS_OPTIONS[status_label],
            }
            try:
                response = requests.post(f"{API_URL}/researchers/", json=payload, timeout=5)
                if response.status_code == 201:
                    data = response.json()
                    st.success(
                        f"🎉 فناور با موفقیت ثبت شد.\n"
                        f"کد ملی: {data.get('national_code')} | "
                        f"نام: {data.get('full_name')} | "
                        f"مرتبه علمی: {data.get('academic_rank')} | "
                        f"موسسه: {data.get('university_id')}"
                    )
                    st.toast("✅ فناور جدید ثبت شد.", icon="🧑‍🔬")
                else:
                    detail = "خطای ناشناخته."
                    try:
                        detail = response.json().get("detail", detail)
                    except ValueError:
                        pass
                    st.error(f"❌ خطا در ثبت فناور: {detail}")
            except requests.exceptions.ConnectionError:
                st.error("خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است.")
            except requests.exceptions.Timeout:
                st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
            except Exception as e:
                st.error(f"خطا در ارسال اطلاعات به سرور: {e}")


## File: dashboard\views\university_entry_page.py
------------------------------
# File: views/university_entry_page.py
"""Phase 4 - New University / Executing Institution registration form."""
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api/v1"

# ─── Aggressive RTL override + compact Persian theme ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@100..900&display=swap');
* { font-family: 'Vazirmatn', sans-serif !important; }
.block-container, .stTextInput, .stNumberInput, .stSelectbox, .stCheckbox, p, div {
    direction: rtl !important;
    text-align: right !important;
}
[data-testid="stSidebarNav"] span {
    direction: rtl !important;
    text-align: right !important;
    font-size: 1.05rem !important;
}
h1 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; padding: 0 !important; }
h2, h3 { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; padding: 0 !important; }
hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("🏫 فرم ثبت موسسه مجری جدید")

IRAN_PROVINCES = [
    "تهران", "اصفهان", "فارس", "خراسان رضوی", "آذربایجان شرقی", "مازندران", "گیلان",
    "کرمان", "یزد", "البرز", "قم", "سمنان", "هرمزگان", "بوشهر", "سیستان و بلوچستان",
    "لرستان", "همدان", "کردستان", "کرمانشاه", "ایلام", "خوزستان", "چهارمحال و بختیاری",
    "کهگیلویه و بویراحمد", "گلستان", "آذربایجان غربی", "اردبیل", "زنجان", "قزوین",
    "مرکزی", "خراسان شمالی", "خراسان جنوبی", "سایر",
]

UNIVERSITY_TYPES = [
    "دانشگاه دولتی",
    "دانشگاه آزاد",
    "دانشگاه غیرانتفاعی",
    "پژوهشگاه",
    "پارک علم و فناوری",
    "شرکت دانش بنیان",
    "موسسه آموزش عالی",
]

with st.form("university_entry_form", clear_on_submit=False):
    st.subheader("۱. اطلاعات موسسه")

    national_id = st.text_input("🪪 شناسه ملی موسسه:", placeholder="مثال: 14001234567")
    name = st.text_input("🏛️ نام کامل موسسه/دانشگاه:")

    col1, col2 = st.columns(2)
    with col1:
        province = st.selectbox("🗺️ استان محل استقرار:", options=IRAN_PROVINCES)
    with col2:
        university_type = st.selectbox("🏷️ نوع موسسه:", options=UNIVERSITY_TYPES)

    is_active = st.checkbox("✅ وضعیت فعالیت: فعال / غیرفعال", value=True,
                            help="تیک خورده = فعال، بدون تیک = غیرفعال")

    submitted = st.form_submit_button("✅ ثبت موسسه", type="primary")

    if submitted:
        if not national_id.strip() or not name.strip():
            st.error("لطفاً شناسه ملی و نام موسسه را تکمیل کنید.")
        else:
            payload = {
                "national_id": national_id.strip(),
                "name": name.strip(),
                "province": province,
                "university_type": university_type,
                "is_active": is_active,
            }
            try:
                response = requests.post(f"{API_URL}/universities/", json=payload, timeout=5)
                if response.status_code == 201:
                    data = response.json()
                    st.success(
                        f"🎉 موسسه با موفقیت ثبت شد.\n"
                        f"شناسه ملی: {data.get('national_id')} | "
                        f"نام: {data.get('name')} | "
                        f"نوع: {data.get('university_type')} | "
                        f"استان: {data.get('province')} | "
                        f"وضعیت: {data.get('status')}"
                    )
                    st.toast("✅ موسسه جدید ثبت شد.", icon="🏫")
                else:
                    detail = "خطای ناشناخته."
                    try:
                        detail = response.json().get("detail", detail)
                    except ValueError:
                        pass
                    st.error(f"❌ خطا در ثبت موسسه: {detail}")
            except requests.exceptions.ConnectionError:
                st.error("خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است.")
            except requests.exceptions.Timeout:
                st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
            except Exception as e:
                st.error(f"خطا در ارسال اطلاعات به سرور: {e}")


## File: Docs\Phase1_Complete.md
------------------------------
# سند جامع فاز اول توسعه سامانه مالی ساتع (SATE\_Fin\_Dev)

موضوع: معماری پایگاه داده، زیرساخت داده‌ها (ETL) و استقرار منطق پایه مالی  
نسخه: v0.2.0-core-db-completed

## ۱. مقدمه و کلیات پروژه

پروژه SATE\_Fin\_Dev یک سامانه مدیریت مالی و حسابداری تعهدی است که با هدف رصد، تجمیع و محاسبه دقیق اعتبارات تکلیفی، واریزی‌ها، قراردادهای پژوهشی و پرداختی‌های مرتبط با مشمولین قانون بودجه توسعه می‌یابد.  
در فاز اول (MVP)، تمرکز بر روی انتقال داده‌های خام (فایل‌های Excel Wide-Format و CSV)، پاک‌سازی آن‌ها، و استقرار یک پایگاه داده رابطه‌ای (Relational) یکپارچه و بهینه بوده است.

## ۲. زیرساخت و محیط توسعه (Environment Setup)

* محیط مجازی: ایزوله‌شده با استفاده از Conda (sate\_env).  
* پایگاه داده: PostgreSQL (دیتابیس sate\_db).  
* ابزارهای توسعه (Stack): پایتون (Python)، موتور ORM دیتابیس (SQLAlchemy)، ابزار پردازش داده‌ها (Pandas) و کتابخانه تبدیل تاریخ (jdatetime).  
* مدیریت نسخه: اتصال موفق به GitHub با رعایت اصول امنیتی (.gitignore برای فایل‌های حساس .env و data).

## ۳. معماری پایگاه داده و جداول (Database Schema & Relationships)

تمامی جداول به ویژگی SoftDeleteMixin (حذف منطقی) مجهز شده‌اند تا از حذف فیزیکی و غیرقابل بازگشت داده‌های مالی جلوگیری شود. روابط کلید خارجی (Foreign Keys) با دقت پیاده‌سازی شده‌اند:

1. جدول مشمولین (employers): *جدول Master (پدر)*  
   * کلید اصلی: classification\_code (شماره طبقه‌بندی).  
   * فیلدهای کلیدی: نام مشمول، نوع مشمول (Mother/Subsidiary/Independent)، استان، و ستون افزوده شده affairs\_category (عنوان امور \- برای گزارش‌گیری‌های کلان).  
2. مدیریت بودجه و اعتبارات (deposits): تبدیل ساختار Wide به Long با معماری Master-Detail:  
   * جدول اعتبارات تکلیفی (annual\_mandates): متصل به employers. نگهداری اعتبار ابلاغی در هر fiscal\_year.  
   * جدول فیش‌های واریزی (deposit\_receipts): متصل به employers. ثبت جزئیات دقیق مبالغ واریز شده به حساب صندوق در هر سال.  
3. جدول دانشگاه‌ها/موسسات اجرایی (universities): *جدول پایه*  
   * کلید اصلی: national\_id (شناسه ملی موسسه).  
   * فیلدهای کلیدی: نام موسسه، استان، نوع موسسه و وضعیت.  
4. جدول فناوران/مجریان (researchers): *فرزند دانشگاه‌ها*  
   * کلید اصلی: national\_code (کد ملی).  
   * کلید خارجی: university\_id (متصل به جدول دانشگاه‌ها).  
   * فیلدهای کلیدی: نام، ایمیل، موبایل، درجه علمی و وضعیت.  
5. جدول قراردادها (contracts): *قلب تپنده و نقطه اتصال (Junction Table)*  
   * کلید اصلی: tracking\_code (کد رهگیری).  
   * کلیدهای خارجی (۳ اتصال همزمان): \- employer\_code (کارفرما)  
     * university\_id (دانشگاه مجری)  
     * researcher\_id (فناور/استاد)  
   * فیلدهای کلیدی: شماره قرارداد، مبلغ کل، تاریخ قرارداد (میلادی)، proposal\_id (برای توسعه‌های آینده).  
6. جدول پرداختی‌ها (payments): *ثبت تراکنش‌ها*  
   * کلید اصلی: tracking\_code (کد رهگیری پرداخت).  
   * کلید خارجی: contract\_tracking\_code (متصل به قراردادها).  
   * فیلدهای کلیدی: سری پرداخت، مبلغ پرداختی، شماره و تاریخ ابلاغ نامه، attachment\_path (مسیر پیوست‌ها).

## ۴. قواعد محاسباتی و منطق تجاری (Core Financial Logic)

در این فاز، چند تصمیم حساس برای تضمین یکپارچگی محاسبات (Data Integrity) اتخاذ شد که باید در داشبوردها و توسعه API مد نظر قرار گیرند:

* تطبیق مقیاس پولی (Base Unit): تمامی ارقام مالی که در اکسل بر حسب «میلیارد ریال» بودند، در مرحله ETL در $10^9$ ضرب شدند. دیتابیس تمامی مبالغ را به عنوان «ریال پایه» با تایپ Numeric(22, 0\) ذخیره می‌کند تا از خطای اعشار و سرریز جلوگیری شود.  
* استانداردسازی تاریخ‌ها: پایگاه داده فقط تاریخ‌های میلادی (Gregorian) را می‌شناسد. تاریخ‌های شمسی در زمان Import توسط jdatetime به میلادی تبدیل شده‌اند. (در لایه فرانت‌اند/داشبورد باید مجدداً به شمسی رندر شوند).  
* سال مالی در برابر سال نقدینگی (Funding Year vs. Payment Year) \- \[بسیار حیاتی\]: در محاسبه مانده حساب مشمولین، سال پرداخت (payment\_year) بی‌اهمیت است. محاسبات دقیق مالی، تفریق پرداختی‌ها از اعتبارات بر اساس سالِ تأمین اعتبار (funding\_year) است. (مثال: پرداختی‌های سال ۱۴۰۴ که از محل اعتبار ۱۴۰۲ بوده‌اند، باید از مانده حساب سال ۱۴۰۲ کسر شوند).

## ۵. استراتژی‌های مهندسی داده (ETL Pipelines)

اسکریپت‌های انتقال داده (موجود در پوشه scripts/) با ویژگی‌های زیر توسعه یافتند:

* جلوگیری از مشکل N+1 Query: در اعتبارسنجی کلیدهای خارجی (نظیر چک کردن وجود دانشگاهِ یک فناور)، به جای کوئری‌های تک‌به‌تک، شناسه‌های مرجع در حافظه (یک Set در پایتون) بارگذاری شده و تطبیق با پیچیدگی O(1) انجام می‌شود.  
* پاک‌سازی داده‌ها (Data Cleaning): فیلتر کردن ردیف‌های دارای ارورهای اکسلی مثل \#REF\!، حذف کاما از ارقام ریالی، و تبدیل ایمن مقادیرِ خالی (NaN) به Null در دیتابیس.  
* اسکریپت اثبات مفهوم (PoC): اسکریپت generate\_financial\_report.py با استفاده از Pandas توسعه یافت که صحت منطق تجاری و کسر پرداختی‌ها از اعتبارات (بر اساس Funding Year) را تأیید کرده و خروجی موفق در results/ ایجاد نمود.

وضعیت فعلی برای شروع فاز ۲: لایه ذخیره‌سازی داده (Data Persistence Layer) صددرصد تکمیل و پایدار است. آماده ورود به توسعه موتور محاسبات تحلیلی (BI)، لایه رابط برنامه‌نویسی (API) و طراحی داشبوردهای مدیریتی می‌باشیم.



## File: Docs\Phase2_Start.md
------------------------------
# سند نقشه راه و معماری کلان (Roadmap & Blueprint)

پروژه: سامانه مدیریت مالی و حسابداری تعهدی ساتع (SATE\_Fin\_Dev)  
موقعیت فعلی: پایان فاز اول (تکمیل لایه پایگاه داده و ETL)  
هدف سند: ترسیم مسیر توسعه فازهای ۲ تا ۵ تا رسیدن به یک محصول نهایی (Production-Ready)

## فاز ۲: توسعه هسته محاسباتی و لایه API (Backend & Business Logic)

اکنون که داده‌ها با موفقیت در دیتابیس مستقر شده‌اند، باید بستری فراهم کنیم تا این داده‌ها به صورت زنده، پردازش شده و در اختیار لایه‌های نمایشی قرار گیرند.

* تکنولوژی پیشنهادی: فریم‌ورک FastAPI (به دلیل سرعت بالا، مستندسازی خودکار و سازگاری عالی با SQLAlchemy) و Pydantic برای اعتبارسنجی داده‌ها.  
* اقدامات کلیدی:  
  1. طراحی موتور محاسبات مالی (Financial Engine): تبدیل اسکریپت گزارش‌گیری فعلی به توابع (Functions) زنده. این توابع در لحظه میزان پرداختی‌ها را بر اساس funding\_year (سال تأمین اعتبار) از mandated\_amount (اعتبار تکلیفی) کسر می‌کنند.  
  2. توسعه Endpoint های RESTful: ساخت مسیرهایی برای دریافت اطلاعات (مثلاً GET /api/employers/{id}/balance برای دریافت مانده یک کارفرما).  
  3. مدیریت تاریخ‌های شمسی: تعبیه توابع jdatetime در لایه API تا تمام تاریخ‌های میلادیِ دیتابیس، در خروجی API به صورت شمسی و خوانا (YYYY/MM/DD) به کاربر نمایش داده شوند.

## فاز ۳: هوش تجاری و داشبوردهای مدیریتی (BI & Data Visualization)

هدف این فاز، تبدیل اعداد خام و JSONها به نمودارهای تعاملی و داشبوردهای مدیریتی برای تصمیم‌گیری است.

* تکنولوژی پیشنهادی: Streamlit (بهترین و سریع‌ترین گزینه برای داشبوردهای مبتنی بر داده در پایتون) یا ترکیب React/Vue.js در صورت نیاز به یک وب‌سایت کاملاً سفارشی.  
* اقدامات کلیدی:  
  1. داشبورد کلان (Executive Dashboard): نمایش مجموع اعتبارات تکلیفی کل کشور، مجموع واریزی‌ها به صندوق و مانده کل سیستم.  
  2. داشبورد مشمولین (Employer View): صفحه‌ای که با انتخاب نام یک شرکت/وزارتخانه، نمودار میله‌ای مقایسه اعتبارات ابلاغی با پرداختی‌های واقعی آن‌ها را به تفکیک سال مالی نشان دهد.  
  3. داشبورد قراردادها و مجریان: رهگیری اینکه کدام دانشگاه‌ها یا فناوران بیشترین حجم ریالی قراردادها را به خود اختصاص داده‌اند.

## فاز ۴: احراز هویت، امنیت و کنترل دسترسی (Security & IAM)

یک سامانه مالی بدون سطوح دسترسی معنایی ندارد. ما باید مشخص کنیم چه کسی مجاز به دیدن چه اطلاعاتی است.

* تکنولوژی پیشنهادی: توکن‌های JWT (JSON Web Tokens) و رمزنگاری Passwords (مثلاً bcrypt).  
* اقدامات کلیدی:  
  1. تعریف نقش‌های کاربری (Role-based Access): نظیر Admin (مدیر کل سیستم)، Employer (نماینده شرکت مشمول) و University (نماینده دانشگاه).  
  2. اعمال فیلترهای امنیتی: مثلاً شرکت توانیر (پس از لاگین) فقط بتواند قراردادها و پرداختی‌های مربوط به خودش را ببیند و به داده‌های شرکت گاز دسترسی نداشته باشد.

## فاز ۵: توسعه فیچرهای جدید و استقرار نهایی (Expansion & Deployment)

تکمیل زنجیره ارزش سامانه و قرار دادن آن بر روی سرور واقعی.

* اقدامات کلیدی (توسعه):  
  1. افزودن جدول پیشنهاده‌ها (Proposals): اتصال proposal\_id در جدول قراردادها به جدول جدید پیشنهاده‌ها.  
  2. مدیریت فایل‌ها و پیوست‌ها: فعال‌سازی قابلیت آپلود فایل (Upload) برای ستون attachment\_path در پرداختی‌ها (ذخیره تصاویر نامه‌ها یا فیش‌های واریزی در سرور).  
* اقدامات کلیدی (استقرار \- DevOps):  
  1. کانتینرسازی سیستم با Docker (برای اجرای بی‌دردسر روی هر سروری).  
  2. تنظیم وب‌سرور Nginx یا Gunicorn.  
  3. انتقال پروژه از محیط Local (کامپیوتر شما) به یک سرور ابری (Cloud Server) لینوکسی برای دسترسی کاربران نهایی.

### سخن پایانی معمار سیستم:

مسیر پیش رو از یک "پایگاه داده استاتیک" به یک "سامانه زنده و پویای مالی" است. استراتژی ما در فاز بعدی (در چت جدید)، شروع مقتدرانه فاز ۲ (طراحی API و توابع محاسبات مالی) خواهد بود.  
این سند، نقشه راه ماست. هر زمان که آماده بودید، این سند و سند قبلی را در یک چت جدید بارگذاری کنید و فرمان شروع لایه Backend را صادر کنید\!  


## File: Docs\Phase3_Dashboard_Complete.md
------------------------------
# Phase 3: Dashboard Implementation - Complete ✅

## Overview
Successfully created a comprehensive Streamlit dashboard for visualizing and debugging financial calculations for each employer in the SATE system.

## Deliverables

### 1. Dashboard Application (`dashboard/app.py`)
A complete, production-ready Streamlit application with the following features:

#### Core Functionality
- **Employer Selection**: Dropdown to select any active employer by classification code
- **Hierarchical Support**: Automatically includes subsidiary data for Mother-type employers
- **Multi-year Analysis**: Aggregates financial data across all fiscal years
- **Real-time Calculations**: Computes balance using the formula:
  ```
  Balance = (Total Deposits + Transfers In) - (Total Payments + Transfers Out)
  ```

#### UI Components
1. **Page Header**: Persian title with emoji icon
2. **Employer Info Cards**: Display employer type, province, and upper organization
3. **KPI Metrics** (6 cards):
   - اعتبار تکلیفی (Mandated Amount)
   - مجموع واریزی (Total Deposits)
   - هزینه کرد (Payments)
   - انتقال ورودی (Transfers In)
   - انتقال خروجی (Transfers Out)
   - مانده واقعی (Actual Balance)
4. **Annual Details Table**: Year-by-year breakdown with Persian column names
5. **Trend Chart**: Line chart showing deposits, payments, and balance over time

#### Technical Features
- **Database Integration**: Uses SQLAlchemy ORM with proper session management
- **Soft Delete Filtering**: Only shows non-deleted records
- **Number Formatting**: Comma-separated integers (Persian-friendly)
- **Error Handling**: Graceful handling of empty data
- **Wide Layout**: Optimized for financial data display
- **Responsive Design**: Works on different screen sizes

### 2. Documentation

#### `dashboard/README.md`
Comprehensive Persian documentation covering:
- Feature descriptions
- Balance calculation formula
- Usage instructions
- Code structure explanation
- Data sources
- Future enhancement suggestions

#### `dashboard/QUICKSTART.md`
Quick start guide in Persian with:
- Installation commands
- Running instructions
- Troubleshooting tips
- Advanced options

### 3. Dependencies
Updated `requirements.txt` to include:
```
pandas
openpyxl
SQLAlchemy
python-dotenv
psycopg2-binary
jdatetime
streamlit
```

## Data Integration

The dashboard queries the following tables:
1. **employers** - Employer master data
2. **annual_mandates** - Mandated budget amounts
3. **deposit_receipts** - Deposit transactions
4. **contracts** - Contract records
5. **payments** - Payment transactions
6. **credit_transfers** - Credit transfer records

## Key Implementation Details

### Hierarchical Aggregation
For Mother-type employers:
```python
if employer.employer_type == 'Mother':
    codes_to_include = [employer_code]
    subsidiaries = db.query(Employer.classification_code).filter(
        Employer.parent_code == employer_code,
        Employer.is_deleted == False
    ).all()
    codes_to_include.extend([s[0] for s in subsidiaries])
```

### Financial Calculation Logic
```python
# Merge all financial data by year
df_merged = df_mandates.merge(df_deposits, on='year', how='outer')
           .merge(df_payments, on='year', how='outer')
           .merge(df_transfers_in, on='year', how='outer')
           .merge(df_transfers_out, on='year', how='outer')
           .fillna(0)

# Calculate balance
df_merged['balance'] = (
    df_merged['deposit_amount'] + df_merged['transfer_in']
) - (
    df_merged['payment_amount'] + df_merged['transfer_out']
)
```

## How to Run

From the project root directory:
```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run the dashboard
streamlit run dashboard/app.py
```

The dashboard will open automatically in your default browser at `http://localhost:8501`

## Testing Checklist

Before deployment, verify:
- [ ] Database connection works (check .env file)
- [ ] Employers dropdown populates correctly
- [ ] KPI metrics display accurate totals
- [ ] Annual table shows all years with correct data
- [ ] Chart renders properly
- [ ] Number formatting is correct (comma-separated)
- [ ] Persian text displays properly (RTL support)
- [ ] Subsidiary aggregation works for Mother employers
- [ ] Soft-deleted records are excluded
- [ ] Empty states handle gracefully

## Performance Considerations

- Queries use proper indexing on foreign keys and year columns
- SQLAlchemy sessions are properly closed in finally blocks
- Pandas operations are efficient with vectorized calculations
- Streamlit caching can be added for frequently accessed data

## Security Notes

- Database credentials are loaded from .env file (never hardcoded)
- SQL injection is prevented by using SQLAlchemy ORM
- No sensitive data is logged or displayed unnecessarily

## Future Enhancements (Suggested)

1. **Filtering**:
   - Date range selector
   - Province filter
   - Employer type filter

2. **Export**:
   - Excel export button
   - PDF report generation

3. **Visualizations**:
   - Interactive Plotly charts
   - Pie charts for budget distribution
   - Comparison mode (multiple employers)

4. **Analytics**:
   - Budget utilization percentage
   - Trend predictions
   - Anomaly detection

5. **Performance**:
   - Implement Streamlit caching
   - Add pagination for large datasets
   - Background data refresh

6. **User Management**:
   - Authentication/authorization
   - User-specific views
   - Audit logging

## Project Status

✅ Phase 1: Database Design and Data Import - Complete
✅ Phase 2: Financial Engine and Calculation Logic - Complete
✅ Phase 3: Dashboard for Visualization and Debugging - Complete

**Next Steps**: Begin Phase 4 (if planned) or move to production deployment and user testing.

## Files Created/Modified

```
dashboard/
├── app.py              # Main Streamlit application (10.9 KB)
├── README.md           # Comprehensive documentation (4.5 KB)
└── QUICKSTART.md       # Quick start guide (1.9 KB)

requirements.txt        # Updated with streamlit dependency
```

## Summary

The Phase 3 dashboard provides a powerful, user-friendly interface for:
- Viewing financial summaries for each employer
- Debugging calculation logic
- Identifying data inconsistencies
- Supporting financial decision-making
- Generating visual reports

The implementation is clean, well-documented, and ready for immediate use by the SATE management team.


## File: Docs\SATE_Living_Documentation.md
------------------------------
# SATE Financial System — Living Documentation
### سامانه مالی نظارت بر تأمین اعتبار طرح‌های پژوهشی ساتع

**Status:** MVP — Phase 4 complete (data-entry forms), entering demo phase.
**Maintenance rule:** This document is updated automatically after every coding task completed in this workspace (see [Continuous Update Protocol](#continuous-update-protocol) at the bottom). Treat it as the current source of truth; if it conflicts with the code, the code wins and this file should be corrected in the same turn.

---

## 1. Environment & Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Backend framework | FastAPI |
| Frontend framework | Streamlit (RTL, Vazirmatn font) |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 (declarative, session-based) |
| Environment isolation | Conda environment named `sate_env` |
| Data interchange | pandas + openpyxl (Excel ETL) |
| Calendar handling | `jdatetime` via `core/date_helper.py` |
| Dependencies | `requirements.txt`: pandas, openpyxl, SQLAlchemy, python-dotenv, psycopg2-binary, jdatetime, streamlit |

**Directory layout**

```
core/        connection/session factory (database.py), SoftDeleteMixin, strict Jalali date helper (date_helper.py)
models/      SQLAlchemy ORM models (one file per domain table)
schemas/     Pydantic request/response schemas, one file per API resource
api/v1/      FastAPI routers; api_router.py aggregates per-resource routers under api/v1/endpoints/
services/    Business-logic core — financial_engine.py (balances, locking, dynamic contract status)
dashboard/   Streamlit frontend — app.py (active), app_v2.py (legacy, see §2), views/ (data-entry forms)
scripts/     ETL loaders, one-off migrations, and reporting utilities (see §4)
data/        Source Excel workbooks consumed by scripts/import_*.py
results/     Output of reporting scripts (generate_financial_report.py, generate_contract_status_report.py)
Docs/        Project documentation, including this file
```

Configuration is loaded from a local `.env` (not committed) via `python-dotenv`; `DATABASE_URL` is required and `core/database.py` raises `RuntimeError` at import time if it is missing. The engine uses `pool_pre_ping=True` and a 5s `connect_timeout`.

---

## 2. Frontend Architecture Note

`dashboard/app.py` is the **active, maintained entry point** (`streamlit run dashboard/app.py`, per `dashboard/README.md`/`QUICKSTART.md`). It builds a multi-page `st.navigation` shell with two groups:

- **داشبوردهای مدیریتی (Management dashboards):** a two-tab view — Tab 1 (`render_tab1`) is a single-employer balance sheet (KPI cards, detail table, bar/waterfall charts, Excel export); Tab 2 (`render_tab2`) is the macro/executive summary across all employers, sourced from `services.financial_engine.get_all_employers_financials`. The dashboard tabs query the database **directly** via SQLAlchemy — they do not go through the FastAPI layer.
- **فرم‌های ورود اطلاعات (Data-entry forms):** `views/batch_payments_page.py`, `views/contract_entry_page.py`, `views/contract_edit_page.py`, `views/university_entry_page.py`, `views/researcher_entry_page.py`. These forms **do** call the FastAPI backend over HTTP (`API_URL = "http://127.0.0.1:8000/api/v1"`), so both `uvicorn main:app` and `streamlit run dashboard/app.py` must be running for the forms to work.

`dashboard/app_v2.py` is a **frozen, legacy single-page prototype** — it predates the navigation/forms refactor, duplicates Tab 1's logic almost verbatim, and has not been touched since its one initial commit. Treat it as reference-only; do not extend it. `dashboard/README.md`, `QUICKSTART.md`, and `CHANGELOG.md` describe the pre-refactor single-page app and are stale relative to current `app.py` — they need an update pass to document the navigation shell and the four data-entry forms.

**Batch payment cart pattern (database-backed, since 2026-08-07):** `views/batch_payments_page.py` no longer keeps a client-side `st.session_state.payment_cart` — the cart *is* the `payments` table. Adding a row calls `POST /payments/draft`, which inserts a `Payment` with `status="Draft"` immediately (surviving a browser reload) and hard-blocks (HTTP 400) if the employer's real balance can't cover it, since `calculate_real_balance` counts `Draft` rows exactly like `Final` ones (§3.3) — funds are reserved the instant a draft is created, not deferred to submission time. The table (`GET /payments/drafts?series=...`) and row deletion (`DELETE /payments/draft/{tracking_code}`, a soft-delete) always reflect the database, not local state. "تأیید نهایی لیست" calls `POST /payments/finalize-batch`, a pure status transition (`Draft` → `Final` for every row in the series) that does not change any balance, since both statuses were already counted identically.

**Enriched draft/finalize responses (since 2026-08-07):** every payment-draft endpoint response (`POST /payments/draft`, `GET /payments/drafts`, the `finalized_payments` array in `POST /payments/finalize-batch`) is built from one joined query across `Payment`→`Contract`→`Employer`→`University` (`api/v1/endpoints/payments.py`'s `_enriched_payment_query`, all `outerjoin`s on a single FK→PK so there is never row fan-out) plus a per-employer/funding-year `employer_balance_after` computed by `_compute_balances_after` — grouped so only one `calculate_real_balance` call happens per distinct `(employer_code, funding_year)` pair in the result set, never one per row. `POST /payments/draft` additionally returns `employer_balance_before` (reusing values `validate_payment_impact` already computed, no extra query). The frontend's drafts table and the finalize Excel export both map this enriched shape onto one fixed Persian header order via a single shared `_to_persian_row`/`_build_dataframe` helper pair — on-screen numbers are comma-formatted display strings, the Excel export keeps raw numeric values (same convention as `dashboard/app.py`'s existing Excel exports, for further in-Excel calculation).

**`st.table`, never `st.dataframe`, for Persian-labeled financial tables (hard rule, since 2026-08-08):** `st.dataframe` renders every cell on an HTML `<canvas>` — canvas content ignores all page CSS (`font-family`, `direction: rtl`), and a comma-grouped Western-digit number inside an RTL-directed context is prone to Unicode bidi reordering in the browser (numbers visually scramble). `dashboard/app.py`'s existing tables already avoid this by using `st.table` (a real HTML `<table>`, styled via this file's own `table, th, td, .stTable` CSS block) plus `to_persian_numbers()`-style digit conversion for on-screen display. `batch_payments_page.py` initially used `st.dataframe` and hit both bugs at once (wrong font, scrambled balance column) before being corrected — any new Persian-labeled table in this app must follow the same `st.table` + Persian-digit-string pattern, not `st.dataframe`, regardless of `st.dataframe`'s nicer built-in sort/filter/column-visibility chrome.

---

## 3. Database Architecture

### 3.1 Soft-delete enforcement (mandatory, no exceptions)

Every model mixes in `core.database.SoftDeleteMixin`, which adds an indexed `is_deleted: Boolean` column (`default=False, nullable=False`). **All** queries, joins, and validation lookups across `api/`, `services/`, and `dashboard/` explicitly filter `is_deleted == False` — records are never physically deleted, preserving financial audit history. New code (endpoints, services, scripts, dashboard queries) must add this filter to every query against a soft-deletable table, including join conditions (see `api/v1/endpoints/contracts.py`'s `search_contracts`, which filters `is_deleted == False` on all four joined tables, not just the primary one).

### 3.2 Core models

| Table (model) | Purpose | Key relationships |
|---|---|---|
| `employers` (`Employer`) | مشمولین — organizations under funding mandate. `employer_type` ∈ {Mother, Subsidiary, Independent} (CHECK constraint). Self-referential `parent_code` FK groups Subsidiaries under a Mother. | Parent of `contracts`, `deposits`/`annual_mandates`/`deposit_receipts`, `credit_transfers`. |
| `universities` (`University`) | دانشگاه‌ها — executing institutions. `national_id` PK. | Parent of `researchers`, referenced by `contracts`. |
| `researchers` (`Researcher`) | فناوران — individual researchers, one-to-many under a university. `national_code` PK. | FK to `universities.national_id`. |
| `contracts` (`Contract`) | The central junction table — links one employer, one university, one researcher. `tracking_code` PK, `total_amount` as `Numeric(22,0)` (whole Rials, no decimals). | FKs to `employers`, `universities`, `researchers`; parent of `payments`, `credit_transfers`. |
| `payments` (`Payment`) | پرداختی‌ها — disbursements against a contract. Carries both `payment_year` (cash-flow year) and `funding_year` (budget-consumption year) — see §5.1 for why these must never be conflated. | FK to `contracts.tracking_code`. |
| `deposits` (`Deposit`) | Aggregate mandate-vs-deposit summary per (employer, fiscal_year); unique constraint enforces one row per pair. Appears less actively used than the split `AnnualMandate`/`DepositReceipt` tables below — verify before building new features on it. | FK to `employers`. |
| `annual_mandates` (`AnnualMandate`) | تکالیف قانونی — the legally mandated budget amount per employer per fiscal year. Unique on `(employer_code, fiscal_year)`. | FK to `employers` (`ondelete="CASCADE"`). |
| `deposit_receipts` (`DepositReceipt`) | واریزهای فیزیکی — individual deposit receipts per employer per fiscal year (detail records, not aggregated). | FK to `employers` (`ondelete="CASCADE"`). |
| `credit_transfers` (`CreditTransfer`) | انتقالات اعتباری — reallocates unspent funds from a source employer to a destination employer's contract (Tabsare 2, ماده 5), without mutating deposit/payment history. Defaults `destination_employer_code` to the Secretariat (`"128342"`). | FKs to `employers` (source + destination) and `contracts`. |

**Balance formula (single source of truth, `services/financial_engine.py`):**

```
real_balance(employer, funding_year) =
      Σ DepositReceipt.deposit_amount   (employer + its Subsidiaries if Mother)
    + Σ CreditTransfer.amount           (destination = employer)
    − Σ CreditTransfer.amount           (source = employer or its Subsidiaries)
    − Σ Payment.amount                  (via Contract.employer_code == employer, funding_year match)
```

For a `Mother` employer, deposits/transfers/payments are rolled up across itself + all `Subsidiary` employers whose `parent_code` matches; `Independent` and `Subsidiary` employers use only their own rows.

### 3.3 Transaction safety & concurrency

- **Pessimistic locking is mandatory for financial inserts.** `services/financial_engine.py` provides `lock_active_contracts`/`lock_active_employers`/`lock_active_contract_and_employer`, all using `.with_for_update()` and sorting keys before locking to give concurrent transactions a consistent lock order (deadlock avoidance). Any new code path that reads a balance and then writes a payment/transfer in the same logical operation must lock first and keep the same session/transaction open through the write.
- **Negative balances are a HARD BLOCK, not a warning (superseded FR-18/19/20, 2026-08-07).** The original "warn but allow" MVP rule has been explicitly overridden by product decision. `services.financial_engine.validate_payment_impact` now raises `InsufficientFundsError` (a `ValueError` subclass, so existing `except ValueError` call sites still catch it, while callers needing to distinguish "insufficient funds" from "contract not found" can match the specific type) whenever `current_balance - amount < 0`, instead of returning `is_negative=True`. Both `POST /payments/draft` and `POST /payments/validate` translate this into HTTP 400 with the exact deficit in the message. There is no remaining code path that allows a payment to be registered against an insufficient balance — the old `bulk-submit`/`validate-draft` warning-only endpoints (see below) were removed along with the old cart, not merely reimplemented.
- **Draft payments reserve funds instantly.** `Payment.status` (`"Draft"` or `"Final"`, added by `scripts/add_payment_status_column.py`) is read by `calculate_real_balance`'s payment-sum query as `status IN ('Final', 'Draft')` — a staged-but-not-yet-finalized draft counts against the employer's balance exactly like a confirmed payment. This is what makes the hard block meaningful across a multi-row batch entered over multiple requests/days (§2's batch cart): a second draft against the same employer/year is checked against a balance that already reflects the first draft, without any special "pending batch amount" parameter needed (the old `pending_cart_amount` field is gone — the reservation is now unconditional and server-side). Finalizing a batch (`POST /payments/finalize-batch`) is consequently a pure status flip with zero balance impact, since `Draft` and `Final` were already counted identically.
- **ETL bulk imports are a deliberate exception.** `scripts/import_payments_upsert.py` (and other `payments`-writing ETL scripts) insert with the model's default `status="Final"` and keep their own FR-20-style advisory-only balance warning (§5, 2026-08-07 entry) — they do not call `validate_payment_impact` and are not hard-blocked. This asymmetry (interactive entry blocks, historical bulk reconciliation warns) was not explicitly revisited when the hard-block policy was introduced; flag for product sign-off if bulk imports should also be blocked, since as-is a large historical data load can still legitimately drive a balance negative without being rejected.

### 3.4 Business rule: contract-eligible employer types

`api/v1/endpoints/contracts.py` enforces `ALLOWED_CONTRACT_EMPLOYER_TYPES = {"Mother", "Independent"}` when creating a contract — a `Subsidiary` employer is rejected with a 400 and a Persian error message. This is the single enforcement point today; any future contract-writing code path (e.g. a bulk contract importer) must apply the same check.

---

## 4. Core Business Logic

### 4.1 Funding-year based balance calculation

All balance/limit calculations key off **`funding_year`** (سال مالی تأمین اعتبار — the fiscal year the budget was drawn from), never `payment_year` (the calendar year cash actually moved). `Payment` carries both fields precisely so payments can be executed late against an earlier year's budget without corrupting that year's balance. Any new report or dashboard metric touching money must group/filter by `funding_year`, not `payment_date`/`payment_year`, unless it is explicitly a cash-flow (not budget) report.

### 4.2 Strict Jalali calendar parsing

`core/date_helper.py` exposes `parse_strict_jalali_date`/`parse_strict_jalali_iso` — the **only sanctioned way** to convert a Jalali date string to a Gregorian `datetime.date`/ISO string. It accepts `YYYY/MM/DD` or `YYYY-MM-DD`, uses real `jdatetime` calendar validation (rejects invalid month lengths/leap days), and raises `TypeError`/`ValueError` on bad input — callers must catch and surface a user-facing error rather than let a bad date silently reach the database.

Current adoption is inconsistent — see §4.4 for scripts that bypass this helper with an approximate/incorrect conversion. `dashboard/views/contract_entry_page.py` and `dashboard/views/contract_edit_page.py` are the dashboard files using it correctly (via `parse_strict_jalali_iso`) for the contract-date field on submit.

`core/date_helper.py` only converts Jalali → Gregorian (the direction needed for user input). There is no shared *reverse* (Gregorian → Jalali) helper for displaying a stored date back to the user; `contract_edit_page.py` does this inline with `jdatetime.date.fromgregorian(date=...).strftime("%Y/%m/%d")` to pre-fill the edit form's Jalali date field from the API's Gregorian ISO response. If a third call site needs this, promote it into `core/date_helper.py` rather than copying the inline conversion again.

### 4.3 Dynamic contract status

`get_contracts_with_dynamic_status(db, threshold_year=1402)` in `services/financial_engine.py` computes contract lifecycle status **entirely in SQL** at query time (never persisted to `Contract.status`): `Completed` if total non-deleted payments ≥ `total_amount`; else `Stagnant` if the contract's most recent activity year (max payment `funding_year`, or an approximated Jalali contract-creation year, whichever is greater) is before `threshold_year`; else `Active`. Used by `scripts/generate_contract_status_report.py`.

### 4.4 Known data-integrity risks to track

- **`scripts/import_deposits.py`**: `deposit_amount` scaling (`× 1_000_000_000` billion→base-Rials) is present in `mandated_amount` handling but **commented out** for `deposit_amount`, while the log message still claims the value was scaled. `scripts/process_budgets.py` has the same asymmetry. Needs a data-source audit (is `Deposit_Budget` actually already in base Rials, or is this a bug undercounting deposits by 10^9?) before the next full reload.
- **`scripts/import_deposits.py`**'s `persian_date_to_gregorian()` is a self-admitted MVP approximation (`gregorian_year = jalali_year + 621`, day hard-coded to March 20 regardless of actual month/day) rather than a real conversion — it does not use `core/date_helper.py`. Every historical `DepositReceipt.deposit_date` loaded this way carries a synthetic, likely-inaccurate date.
- **`scripts/chart01_total_trend.py`** imports a `chart_config` module that does not exist in the repository — currently broken/orphaned, cannot run as-is.
- **`scripts/process_budgets.py`** uses a hard-coded absolute Windows path (`C:\Users\pchin\...`) instead of deriving from `__file__` — will break on another machine/environment.
- **`scripts/check_excel.py`** reads `data/University.xlsx` (singular) while `scripts/import_universities.py` reads `data/Universities.xlsx` (plural) — verify which source file is authoritative.
- **Live schema drift from the ORM models, found twice in one day (2026-08-07):** `contracts.attachment_path` and, separately, `payments.payment_date`/`execution_year`/`payment_type` were all missing from the local dev database despite being declared on their respective models — in the payments case, for three columns the model marks `nullable=False`. Both were caught only because a new script's real DB write failed, not by any migration-tracking mechanism (there is no Alembic or similar in this project — schema changes are ad hoc `ALTER TABLE` scripts run manually, per §4.5). **Before the next demo or any new environment/deployment, run `scripts/add_contract_attachment_path.py` and `scripts/add_payment_missing_columns.py` (both idempotent) and audit whether other model columns have similarly never been migrated onto the live table.**

### 4.5 ETL conventions

- Standing reload pipeline: `import_employers.py` → `import_universities.py` → `import_researchers.py` → `import_contracts.py` → `import_deposits.py` → `import_payments.py` → `import_credit_transfers.py` (order matters: later scripts `DROP ... CASCADE` tables that earlier scripts' FKs depend on if run out of order).
- `append_new_mandates.py` (application-level select-then-update/insert) and `import_universities_upsert.py` / `import_researchers_upsert.py` / `import_contracts_upsert.py` (native PostgreSQL `INSERT ... ON CONFLICT DO UPDATE`) are the **evolved, non-destructive patterns** — all replace truncate/reload with merge semantics and are the intended model for future incremental loaders. Per the architectural decision recorded in `Docs/Technical Transition Report_R2.md`, truncate/reload is being phased out now that Phase 4 data-entry forms are live (it would silently wipe user-entered records); prefer a native `ON CONFLICT` upsert (not a Python-side existence check, which is race-prone under concurrent runs) for any new import work. `scripts/import_universities.py`/`import_researchers.py`/`import_contracts.py` (truncate/reload) still exist alongside their `*_upsert.py` counterparts (merge) — pick based on whether a full historical rebuild or an incremental add/update is needed. `import_researchers_upsert.py` and `import_contracts_upsert.py` demonstrate the pattern for a source file missing required FK columns: resolve each one via a pre-loaded name→id lookup (composite-keyed where a bare name is ambiguous, e.g. researcher `(full_name, university_id)`) and skip — never guess — unresolvable rows. `import_contracts_upsert.py` is also the reference example for enforcing the Mother/Independent contract-eligibility rule (§3.4) inside a bulk importer, not just the API layer.
- Current source-file naming convention for the `*_upsert.py` scripts is `data/<Entity>_Add_In.xlsx` (e.g. `Universities_Add_In.xlsx`, `Researchers_Add_In.xlsx`, `Contracts_Add_In.xlsx`), distinct from the historical bulk-load files consumed by the original `import_*.py` truncate/reload scripts (e.g. `Universities.xlsx`, `Researchers.xlsx`). `CreditTransfer_Add_In.xlsx` follows the same naming convention despite its loader (`import_credit_transfers_addin.py`) not being a `*_upsert.py`-suffixed script — see below.
- **Third incremental-loading pattern — application-level insert-ignore** (`import_credit_transfers_addin.py`): used specifically because `credit_transfers` has no business unique constraint (only the auto-increment `id`), so native `ON CONFLICT` has no conflict target — unlike the `*_upsert.py` scripts above, this one deduplicates via an in-memory composite-key set built from active rows and checked/extended per row, and additionally re-validates the source employer's real balance (`services.financial_engine.calculate_real_balance`) before accepting each row, flushing (not committing) after every insert so later rows in the same batch see prior same-batch reservations against the same employer/year. If a future table needs incremental loading but also lacks a natural unique key, this script is the reference pattern rather than `*_upsert.py`.
- Money scaling convention: only the `Budget.xlsx`/`New_Mandates.xlsx` mandate figures are stored in the source as *billions* of Rials and need `× 10^9`; Contracts/Payments/CreditTransfers source files already store raw Rials.

---

## 5. Active Changelog & Action Registry

> Newest entries first. Each entry: date, scope, one-line summary, and any follow-up implications. Appended automatically after every completed coding task in this workspace per the protocol below.

### 2026-08-07
- **Feature:** Added `scripts/import_universities_upsert.py` — a non-destructive ETL loader for `universities` using a native PostgreSQL `INSERT ... ON CONFLICT (national_id) DO UPDATE` (via `sqlalchemy.dialects.postgresql.insert`), replacing the truncate/reload + Python-side existence check pattern used by `scripts/import_universities.py` for this use case. Source: `data/Add_In Universities.xlsx`. On conflict it refreshes `tracking_code`, `name`, `province`, `university_type`, `status`, `city`, `address` and forces `is_deleted = False` (restores soft-deleted rows on re-import). NOT NULL fields (`province`, `university_type`, `status`) fall back to `'نامشخص'`/`'Active'` when blank in the source; rows missing `national_id` or `name` are skipped and logged. All rows are batched into one statement per run for atomicity; in-file duplicate `national_id`s are collapsed to the last occurrence first (PostgreSQL rejects a batch that targets the same conflict key twice). Verified against the local dev DB: ran twice for idempotency (40/40 rows processed both times, no duplicates — table count 769 before/after), and spot-checked a restored record's `province`/`status`/`is_deleted` values.
- **Follow-up implication:** `scripts/import_universities.py` (truncate/reload) and this new upsert script now both target `universities` with different semantics (destructive full rebuild vs. incremental merge) — same pattern split already noted for deposits/mandates in §4.5. Consider documenting a similar "which script for which situation" note in §4.5, and evaluate migrating `import_employers.py`/`import_researchers.py`/`import_contracts.py` to the same upsert pattern now that Phase 4 forms mean truncate/reload risks wiping user-entered data (this concern was already flagged in `Docs/Technical Transition Report_R2.md`).
- **Note:** `scripts/import_universities_upsert.py`'s source path was subsequently updated (outside this session) from `data/Add_In Universities.xlsx` to `data/Universities_Add_In.xlsx`, matching the `<Entity>_Add_In.xlsx` naming convention also used by the researcher source file below. Current source-file names for both scripts are recorded accurately in §4.5.
- **Feature:** Added `scripts/import_researchers_upsert.py` — a non-destructive ETL loader for `researchers` using the same native PostgreSQL `INSERT ... ON CONFLICT (national_code) DO UPDATE` pattern. Source: `data/Researchers_Add_In.xlsx` (327 rows). The source file has no `university_id` column, only a free-text institution name (`دانشگاه / محل خدمت`); the script loads a `{university.name.strip(): national_id}` lookup from the `universities` table once up front and resolves each row against it, skipping (with a logged warning) any row whose institution name doesn't match an active university — `university_id` is a required FK with no safe default. On conflict it refreshes `tracking_code`, `first_name`, `last_name`, `full_name`, `mobile`, `email`, `academic_rank`, `education_level`, `researcher_type`, `status`, `university_id`, and forces `is_deleted = False`. `national_code` is zero-padded to 10 digits (source values were 8–10 digits — Excel drops leading zeros on numeric-looking ID columns); `full_name` is generated by concatenating first/last name. Verified against the local dev DB: ran twice for idempotency (320 upserted / 7 skipped for unmatched institution / 0 invalid-data skips, both runs identical), confirmed the pre-existing ~12,591 researcher rows were untouched (no truncation), and spot-checked a restored record's zero-padded `national_code`, resolved `university_id`, and `is_deleted` value.
- **Data-quality note (resolved same day, see next entry):** 2 distinct institution names in the researcher source file (`دانشگاه علامه طباطبایی`, `دانشگاه صنعتی شریف` — 7 rows total) do not match any active row in `universities` by exact stripped name. Likely a naming/punctuation mismatch (e.g. "دانشگاه" prefix variants) or a genuinely missing university record — worth a manual review before the next import run to recover those 7 researchers, either by adding the missing university rows or fixing the name mismatch at the source.
- **Fix:** Added `scripts/fix_university_names.py`, a one-off migration resolving the data-quality note above. Root cause: `universities` had "علامه طباطبایی" and "صنعتی شریف" stored without the "دانشگاه " prefix used in the Excel exports. The script maps a name substring (chosen to stop just before the character that varies between "ی"/"ئ" spellings) to a canonical exact name, but resolves each rule through a 3-tier lookup rather than blindly applying `LIKE` to every match: (1) exact match on the canonical name → already fixed, no-op; (2) exact match on the substring itself → the precise pre-fix variant, rename; (3) only if neither exact lookup hits, a broader `ILIKE` substring search, which is rejected (logged as ambiguous, left untouched) if it matches more than one active row. This mattered in practice: a naive `ILIKE '%صنعتی شریف%'` matches *two* active universities — the target record and an unrelated "پارک علم و فناوری دانشگاه صنعتی شریف" (Sharif Science & Technology Park, a different organization) — and the 3-tier lookup correctly resolved to the single exact-match target (`national_id=14002830256`) without touching the park record (`national_id=14002830222`). Verified: ran three times — run 1 fixed both records (Allameh Tabataba'i `14003122805` and Sharif `14002830256`); run 2 (before the exact-match-on-canonical-name tier was added) regressed the Sharif rule to a false "ambiguous" skip on re-run, which was caught here and fixed by adding the canonical-name lookup as the first tier; run 3 reported both rules cleanly as "already correct" with zero writes. Re-ran `import_researchers_upsert.py` afterward and confirmed all 327 source rows now upsert successfully (0 skipped for unmatched university, up from 7).
- **Follow-up implication:** This confirms name-based FK resolution (as used by `import_researchers_upsert.py` and any future importer keying off a free-text organization name) is fragile to prefix/spelling drift in `universities.name`. If more such mismatches surface, consider either a dedicated alias/synonym table or normalizing comparisons (e.g. strip common prefixes, normalize ی/ئ) inside the lookup itself rather than fixing source data row-by-row.
- **Feature:** Added `scripts/import_contracts_upsert.py` — a non-destructive ETL loader for `contracts` using the same native PostgreSQL `INSERT ... ON CONFLICT (tracking_code) DO UPDATE` pattern. Source: `data/Contracts_Add_In.xlsx` (60 rows). The source file has no `employer_code`/`university_id`/`researcher_id` columns, only free-text names (`متقاضی`, `دانشگاه`, `فناور`); the script builds three lookups once up front — employer (name → classification_code + employer_type), university (name → national_id), and researcher (composite `(full_name, university_id)` → national_code, since two researchers can share a name across different universities) — and resolves each row in that order (employer → university → researcher, since the researcher lookup needs the resolved `university_id`). **Enforces the standing business rule (§3.4)** that only `Mother`/`Independent` employers may hold a contract: a row whose employer resolves by name but is a `Subsidiary` is treated as an unresolved employer and skipped, since this is a general-purpose importer and the rule has no per-script exception. `تاریخ قرارداد` is parsed with `core.date_helper.parse_strict_jalali_date`; a non-blank value that fails strict validation skips the row (`bad_date`), while a blank cell is accepted as `None` since `contract_date` is nullable. On conflict it refreshes `employer_code`, `university_id`, `researcher_id`, `proposal_id`, `contract_number`, `contract_date`, `total_amount`, `title`, `duration_months`, `status`, and forces `is_deleted = False`; `attachment_path` is intentionally left out of both insert and update (source has no attachment data). Verified against the local dev DB: ran twice for idempotency (57 upserted / 3 skipped for unmatched employer, identical both runs — the 3 all reference the same not-yet-onboarded employer "شرکت نفت فلات قاره ایران"), confirmed the pre-existing contract rows were untouched (1,968 total after, no truncation), and spot-checked a sample record's resolved FKs, parsed Gregorian date, and amount.
- **Bug found & fixed (pre-existing, unrelated to the new script):** Verifying the above via a plain `session.query(Contract)` failed with `psycopg2.errors.UndefinedColumn: column contracts.attachment_path does not exist` — the live dev database's `contracts` table was missing the `attachment_path` column that `models/contract.py` declares and that `dashboard/views/contract_entry_page.py`'s file-upload feature depends on. `scripts/add_contract_attachment_path.py` (an idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, added in an earlier session per §5's 2026-08-07 history) existed specifically to fix this but had evidently never been run against this database instance. Ran it now (safe, additive, non-destructive); confirmed via `information_schema.columns` that the column exists post-fix. **This means any code path doing a full-entity `Contract` query — including `create_contract`'s `db.refresh(contract)` in `api/v1/endpoints/contracts.py` and the contract-entry form's attachment flow — was likely broken against this database until this fix.** Worth double-checking any other deployment/environment for the same drift before the next demo.
- **Feature:** Implemented "Search and Edit Contract" end-to-end (backend + frontend + navigation), letting users fix data-entry errors in already-registered contracts.
  - **Backend** (`api/v1/endpoints/contracts.py`, `schemas/contract_schema.py`): added `GET /contracts/{tracking_code}` (returns a new `ContractDetail` schema — raw FK codes plus all editable fields, for pre-filling the edit form) and `PUT /contracts/{tracking_code}` (accepts a new `ContractUpdate` schema — `ContractCreate` minus `tracking_code`, since the primary key is supplied via the URL path and never changes). Both routes are registered **after** `/search` and `POST /` in the file, since FastAPI/Starlette matches routes in registration order and a `/{tracking_code}` path-param route registered first would shadow the literal `/search` path. `update_contract` reuses `_get_active_contract_parties` (its type hint widened to `ContractCreate | ContractUpdate`) so an update is validated by the exact same active-FK lookup and Mother/Independent employer-type business rule (§3.4) as contract creation — not a separate, potentially-drifting copy of that logic — and reuses the same layered `IntegrityError`/`DataError`/`OperationalError`/`SQLAlchemyError` handling as `create_contract`.
  - **Frontend** (`dashboard/views/contract_edit_page.py`, new file): search (`GET /contracts/search`) → select from a dropdown → auto-fetch full detail (`GET /contracts/{tracking_code}`) → pre-filled `st.form` (employer/university/researcher dropdowns pre-selected via `_index_of`, text/number fields via `value=`, Jalali date reconstructed from the API's Gregorian ISO date) → submit → `PUT /contracts/{tracking_code}`. Attachment is shown read-only (current path or "no attachment" caption); re-uploading a replacement file was left out of scope since the task's focus was fixing data-entry errors (names/amounts/dates/dropdowns), not document management.
  - **Streamlit widget-state bug found and fixed during implementation:** initially keyed each form widget as `f"edit_<field>_{tracking_code}"`. Since Streamlit widgets ignore their `value=`/`index=` argument once their key already has an entry in `session_state`, editing the *same* contract a second time later in one browser session would have silently re-shown the stale values from the first edit instead of freshly fetched data — a real bug, not just a theoretical one, since the natural workflow is "fix a field, save, then reopen the same contract to fix something else." Fixed by adding a `LOAD_SEQ_KEY` counter incremented on every successful fetch and folding it into every widget key (`f"edit_<field>_{tracking_code}_{load_seq}"`), forcing a fresh widget namespace on every load, including a reload of the same contract.
  - **Navigation** (`dashboard/app.py`): registered as `contract_edit_page` under "فرم‌های ورود اطلاعات", between "ثبت قرارداد جدید" and "ثبت موسسه مجری".
  - **Verified end-to-end, not just unit-tested:** `fastapi.testclient.TestClient` was unavailable (`httpx2` not installed in this env), so verification used live servers instead. Found a pre-existing `uvicorn` process already bound to port 8000, started earlier the same day (11:45 AM) — almost certainly the user's own running dev backend serving the *pre-edit* code. Did not kill it blindly: first verified the new routes against a throwaway server on port 8001 (`GET`/`PUT` happy paths, 404 on unknown tracking code, 404 on unresolvable employer, 400 on a `Subsidiary` employer — confirming the business rule is enforced on update too), then — since the feature cannot work at all until the user's real backend serves the new routes — restarted the port-8000 process with the updated code. Then started `streamlit run dashboard/app.py` on port 8501 and drove the actual browser UI end-to-end: searched for a real contract, confirmed all three dropdowns and every text/number field pre-filled with the correct current values (including the Jalali date round-tripping exactly back to its original `1401/12/23`), edited the title and duration, saved, confirmed the success toast and the persisted change via a live re-fetch of the same contract (which also exercised the load-sequence fix above), then restored the test contract's original values via the API. Both the port-8000 backend and the port-8501 Streamlit app were left running afterward so the user can try the feature immediately.
- **Feature:** Added `scripts/import_credit_transfers_addin.py` — an **application-level insert-ignore** loader for `credit_transfers`, distinct from every prior `*_upsert.py` script in this project. `credit_transfers` has no business unique constraint (only the auto-increment `id`), so `INSERT ... ON CONFLICT` has no conflict target to key off; deduplication instead happens in Python against an in-memory set of composite keys `(source_employer_code, destination_employer_code, contract_tracking_code, fiscal_year, amount)` loaded from every active row, extended as each new row is accepted so in-file duplicates are also caught. Source: `data/CreditTransfer_Add_In.xlsx` (3 rows). The fiscal-year column name embeds the year itself and varies between files (e.g. `'انتقال از محل 1402سال مالی'`); `find_fiscal_year_column` locates it via a regex on `'انتقال از محل'`, and `_resolve_fiscal_year` reads the row's cell value first, falling back to a year pattern in the header text only if the cell is blank.
  - **Financial-safety design decision (verified, not just asserted):** before accepting a row, `services.financial_engine.calculate_real_balance` checks the source employer's balance for that fiscal year, per the task's "CRITICAL" requirement. Unlike the original `scripts/import_credit_transfers.py` (which never flushes between rows), this script calls `session.flush()` immediately after each accepted `session.add()` — still inside the same open transaction, so the single end-of-run `session.commit()` / on-exception `session.rollback()` contract is unchanged. This matters because `SessionLocal` is configured with `autoflush=False` (`core/database.py`): without an explicit flush, a second row drawing from the *same* source employer + fiscal year later in the same file would see the *stale pre-batch* balance and could pass validation even though the batch has already committed those funds elsewhere, jointly overdrawing the employer. Confirmed this concretely in a rolled-back test transaction against employer `232000`/fiscal year 1402 (balance 1,001,612,000): a first synthetic row reserving 60% flushed correctly down to 400,644,800, and a second row for 60% of the *original* balance (600,967,200) — which would have wrongly passed against the stale balance — correctly failed against the fresh, flushed balance.
  - Verified against the local dev DB: first run inserted all 3 rows (all FKs valid, balances sufficient — confirmed by direct pre-checks before running); second run correctly skipped all 3 as duplicates (composite-key set grew from 13 to 16). Also exercised `fk_error`, `insufficient_funds`, and `invalid_data` skip paths individually via a temporary scratch Excel file (deleted after the test) monkeypatched in as the source path — each produced the expected skip reason and log message, and none of that scratch data was left in the database (the whole run's rows were either accepted into the real table intentionally or skipped, never partially committed).
- **Feature:** Added `scripts/import_payments_upsert.py` — a non-destructive ETL loader for `payments` using the native PostgreSQL `INSERT ... ON CONFLICT (tracking_code) DO UPDATE` pattern. Source: `data/Payments_Add_In.xlsx` (54 rows). Validates `contract_tracking_code` against a `{contract_tracking_code: employer_code}` lookup built from active contracts (1 row skipped — a row whose payment-tracking-code cell literally contained the placeholder text "محرمانه" and had no contract code at all). Backfills three source-file-absent, model-required columns per the task's explicit fallback rules: `payment_date` <- parsed `notification_date` (row skipped if unparseable — 23/54 rows had a malformed `تاریخ ابلاغ` value like `'3/12/05634'`, not a valid `YYYY/MM/DD` Jalali date; worth a source-data audit, since ~43% of this file's rows were rejected for this reason alone), `execution_year` <- `int(funding_year)`, `payment_type` <- fixed placeholder `"نامشخص"`.
  - **Schema-drift bug found & fixed (pre-existing, unrelated to the new script, same class as the `contracts.attachment_path` incident earlier the same day):** the live `payments` table was missing `payment_date`, `execution_year`, and `payment_type` entirely — all three declared `nullable=False` on `models/payment.py` — causing the first real upsert attempt to fail with `UndefinedColumn` (caught cleanly by the script's `rollback()`, no partial write). Unlike the contracts case, no existing migration script covered this, so one was added: `scripts/add_payment_missing_columns.py`. **Deliberately added the three columns as nullable, not `NOT NULL` matching the model** — 1,277 of the table's 1,420 existing rows have no `notification_date` (the only plausible backfill source for a historical `payment_date`), so retroactively enforcing `NOT NULL` would require fabricating placeholder dates for the majority of payment history, which is a data-policy decision, not an ETL-script implementation detail. Every row this script itself writes always supplies all three columns, so the application-level guarantee holds for new/updated data. **Follow-up decision needed:** choose a backfill strategy for the 1,277 historical rows (or accept `NULL` there permanently) before promoting these columns to `NOT NULL` to match the model exactly.
  - **FR-20 double-counting bug found & fixed during verification (financial logic, not just a display glitch):** the first working run logged 6 negative-balance warnings; an immediate idempotency re-run against the *same, now-committed* data logged 9. Root cause: `services.financial_engine.calculate_real_balance` already sums every active payment in the database — including the 30 rows this script had just committed — so the script's own running-balance projection (added for the same reason as `import_credit_transfers_addin.py`'s flush, to catch multiple new same-batch payments against the same employer/year) was subtracting each row's amount a *second* time for rows that already existed from the prior run's `UPDATE`, not a fresh `INSERT`. Fixed by loading a `{tracking_code: existing_amount}` map (`build_existing_payment_amounts`) up front and adding back any already-committed amount for a row before subtracting its new amount — so an unchanged re-run of the same row nets to zero instead of compounding a phantom deficit on every run. Verified: re-ran four times total after the fix; warning count settled at a stable 6 across repeated runs (previously 6 → 9 → grows unboundedly), row-processing counts (30 processed / 1 FK-skip / 23 bad-date-skip) were already stable across all runs even before this fix — only the advisory warning *count* was affected, not which payments were written or their field values.
  - Verified against the local dev DB: total active `payments` rows went from 1,420 to 1,450 (exactly the 30 newly inserted), spot-checked one record's `payment_date`/`execution_year`/`payment_type` fallback values and its original `notification_date`/`payment_year`/`funding_year`, and confirmed idempotency (identical 30/1/23 split, and post-fix a stable 6 FR-20 warnings) across four consecutive runs.
- **Refactor:** Replaced the batch-payment "cart" system end-to-end — database-backed drafts with a hard balance block, overriding the original FR-18/19/20 "warn but allow" MVP rule. See §2 and §3.3 for the updated reference-doc description; this entry covers what changed and how it was verified.
  - **Schema** (`models/payment.py`, `scripts/add_payment_status_column.py`): added `Payment.status` (`"Draft"`/`"Final"`, Python-side default `"Final"`). Migration adds the column with a SQL-level `DEFAULT 'Final'`, which Postgres also applies to all 1,473 pre-existing rows, so every payment written before this column existed is treated as already confirmed — no behavior change for historical data.
  - **Core logic** (`services/financial_engine.py`): `calculate_real_balance`'s payment-sum query now filters `Payment.status.in_(("Final", "Draft"))` instead of summing unconditionally by status — a draft reserves its amount the instant it exists. Added `InsufficientFundsError(ValueError)` carrying `employer_code`/`funding_year`/`current_balance`/`amount`/`deficit` as structured attributes (not just a message string), so API handlers can build precise error responses without re-deriving the numbers. `validate_payment_impact` now raises this exception whenever the projected balance is negative, instead of returning `is_negative=True` — there is no more success return path for an unaffordable payment.
  - **API** (`api/v1/endpoints/payments.py`, `schemas/payment_schema.py`): removed `POST /payments/validate-draft` and `POST /payments/bulk-submit` along with their schemas (`PaymentBatchValidationRequest/Response`, `PaymentBulkItem`, `PaymentBulkCreate`, `PaymentBulkCreateResponse` — dead code, deleted rather than left unused). Added `POST /payments/draft` (creates one `Draft` payment, hard-blocks HTTP 400 on insufficient funds or duplicate tracking code — the latter via both a fast-path pre-check and an `IntegrityError` catch for the race-condition case), `GET /payments/drafts?series=` (joins through `Contract`/`Employer` so the response carries display-ready `contract_title`/`employer_name`, not just raw codes), `DELETE /payments/draft/{tracking_code}` (soft-delete only, and only if `status == "Draft"` — a `Final` payment sharing the tracking code is untouched), `POST /payments/finalize-batch` (bulk `Draft` → `Final` status flip for a series; idempotent — finalizing an already-finalized or nonexistent series succeeds with `finalized_count: 0` rather than erroring). Kept `POST /payments/validate` (not explicitly mentioned in the task) rather than removing it, but fixed its behavior and docstring to match the new hard-block policy (was previously documented as always returning HTTP 200) — leaving it silently lying about system-wide behavior it no longer had would have been a real, undocumented bug.
  - **Frontend** (`dashboard/views/batch_payments_page.py`, full rewrite): removed `st.session_state.payment_cart` entirely — "add row" calls `POST /payments/draft` directly, the drafts table is `GET /payments/drafts?series=<current series>` re-fetched on every rerun (so it's never stale relative to the database, including across a browser reload), each row has its own 🗑️ delete button calling `DELETE /payments/draft/{tracking_code}`, and finalize calls `POST /payments/finalize-batch`.
  - **Bug found & fixed during frontend testing:** the finalize success message was written as `st.success(...)` immediately followed by `st.rerun()` — `st.success()` is an ephemeral inline element that does not survive an immediately-following rerun (unlike `st.toast()`, which Streamlit specifically designed to persist across one rerun), so the confirmation would never actually have been visible to the user. Fixed using the same `st.session_state`-pending-message pattern already established in `contract_entry_page.py`/`contract_edit_page.py` (store the message, `st.rerun()`, pop and render it at the top of the next run).
  - **Backend verification (thorough, via direct API calls):** confirmed a draft instantly reserves funds (balance dropped from 1,006,150,725 to 506,150,725 immediately after a 500,000,000 draft, before any finalize); confirmed the hard block using the *reserved* balance, not the stale pre-draft one (a second 600,000,000 draft against the same employer/year was rejected with the exact deficit message, `93,849,275` — proving intra-batch deduction works without a client-supplied `pending_cart_amount`); confirmed `GET /payments/drafts?series=` only ever shows successfully-created drafts; confirmed delete restores the reserved balance exactly (back to 1,006,150,725) and a second delete of the same tracking code 404s; confirmed finalize moves status to `Final` without changing the balance and is idempotent on a second call; confirmed `POST /payments/validate` now returns HTTP 400 (not HTTP 200 with a warning) for an unaffordable amount.
  - **Frontend verification:** completed one full, successful UI walkthrough (search a contract → select → fill tracking code/amount/funding year → add → row appears in the drafts table with the correct employer name and amount → delete → row disappears and the balance is restored → re-add → finalize → drafts list empties for that series), which is what surfaced the `st.success`/`st.rerun` bug above. Later repeat attempts to re-verify after the fix hit a browser-automation-specific issue: this environment's synthetic keyboard/value-set events did not reliably reach this particular `st.text_input`'s Streamlit-side session state before a subsequent button click, confirmed via direct DOM inspection (the input's own `.value` was correct, but the search executed as if `search_query` were empty) — an infrastructure/tooling limitation of the test harness, not a defect reproducible through the backend or through the one successful pass. Noted here rather than glossed over, since "verified" should mean what it says.
  - **Cleanup:** found and hard-deleted a stray `Final`-status test payment (`series="15"`, the app's actual default series value) left over from the successful test run above — a synthetic payment sitting in `Final` status would have silently distorted real balance calculations for that employer/contract/year if left in place. Confirmed the employer's balance returned to its exact pre-test baseline (1,006,150,725) after cleanup.
  - Restarted the port-8000 backend (previously serving pre-refactor code) and the port-8501 Streamlit app to pick up all of the above; both left running for continued use.
- **Enhancement:** Enriched the batch-payment drafts/finalize flow with contract/university context, per-payment balance tracking, integer-only amounts, an immediate row-reset after add, a prominent balance-transition message, and an auto-generated Excel export on finalize. See §2's "Enriched draft/finalize responses" note for the reference-doc description of the joined-query/balance-grouping design; this entry covers what changed and how it was verified.
  - **Backend** (`api/v1/endpoints/payments.py`, `schemas/payment_schema.py`): `POST /payments/draft` now returns a new `PaymentDraftCreateResponse` (extends `PaymentDraftResponse`) carrying `employer_balance_before`/`employer_balance_after` alongside the existing fields — both values reused directly from `validate_payment_impact`'s own return, no extra query. `PaymentDraftResponse` itself gained `university_name`, `contract_total_amount`, and `employer_balance_after`. `GET /payments/drafts` and the `finalized_payments` list inside `FinalizeBatchResponse` both use the new `_enriched_payment_query` (one `outerjoin` chain `Payment`→`Contract`→`Employer`→`University`, still exactly one row per payment — no fan-out) and `_compute_balances_after` (groups by `(employer_code, funding_year)`, adds each group's own amounts back onto its already-inclusive `calculate_real_balance` result to recover the pre-group baseline, then walks a running balance forward in `tracking_code` order — one `calculate_real_balance` call per distinct group, not per row).
  - **Frontend** (`dashboard/views/batch_payments_page.py`): amount input switched to strict integer mode (`min_value=0, step=1000000, format="%d", value=0` — all-int arguments put `st.number_input` into integer mode). Added `_apply_pending_row_reset`/`ROW_RESET_KEYS`, the same session-state widget-deletion pattern already used for the finalize message, to clear `batch_search_query`/`batch_contract_choice`/`batch_pay_tracking_code`/`batch_amount`/`batch_funding_year` immediately after a successful add — `batch_series`/`batch_payment_year` are deliberately excluded so the global config survives. The add-success balance message uses the same `st.session_state`-pending-message pattern as the finalize fix from the prior entry (`st.success()` does not survive an immediately-following `st.rerun()`). The drafts table and the finalize Excel export both build their DataFrame via one shared `_build_dataframe`/`_to_persian_row` pair against the exact required header list/order, so the on-screen table and the exported file can never drift apart. Finalize now stores the generated Excel bytes, filename, and DataFrame in `st.session_state[FINALIZE_STATE_KEY]` and the page renders a dedicated "success state" (download button + read-only table + "شروع لیست پرداخت جدید") via an early `st.stop()`, hiding the entry form entirely until the user starts a new list — a `download_button` cannot force a save, so this is the closest UX to "auto-download" Streamlit allows. Per-row delete moved from an inline button-per-row (which the exact fixed header list no longer has room for) to a labeled selectbox + a single delete button below the table.
  - **Backend verification (thorough, via direct API calls):** created two sequential drafts for the same employer/funding_year and confirmed `employer_balance_after` in `GET /payments/drafts` walks the running balance correctly in order (706,150,725 then 506,150,725, matching each draft's own creation-time `employer_balance_before`/`after`) rather than repeating the same final number on every row; confirmed `POST /payments/finalize-batch`'s `finalized_payments` carries the same enriched shape (`contract_total_amount`, `university_name`, correct `employer_balance_after`) with `status` flipped to `Final`.
  - **Frontend verification, working around a recurring known limitation:** the same `st.text_input` keystroke-sync flakiness documented in the prior entry recurred for both the contract-search box and the series field in this session, so the "Add to Batch" happy path (balance message + field reset) could not be re-driven through the live UI this time either — confirmed via direct DOM inspection that this is unchanged tooling behavior (typed values were correct in the DOM but not reflected in the Python-side rerun), not a regression. Rather than stop at "couldn't verify," the parts of the new feature that don't depend on that specific widget were verified for real: created a test draft directly via the API (bypassing the flaky search box), reloaded the page on the **untouched default series value** ("15", so no text field needed changing), and drove the rest of the flow — delete-selectbox rendering with the correct comma-formatted label, the exact-header `st.dataframe` rendering (confirmed present via its toolbar controls; cell content itself is canvas-drawn by Streamlit's grid component and isn't visible to DOM text extraction, so the underlying `_build_dataframe` output was separately confirmed correct by rebuilding it in a plain Python script against the live API response), the finalize button (via JS `.click()`, since `computer`-tool clicks on this specific button also did not register a Streamlit rerun in this session), the "success state" transition (message persisted correctly, download button appeared), and — the deepest check — captured the network request the download button actually fired (`GET /media/<hash>.xlsx`), downloaded that exact file, and opened it with `pandas.read_excel`: headers matched the required list and order exactly, and every value (amounts, `contract_total_amount`, `employer_balance_after`) was numerically correct. This is real, file-level proof the export works, not an assumption from code review.
  - **Cleanup:** found and hard-deleted a second stray `Final`-status test payment under the real default series `"15"` (same hazard as the prior entry — confirmed the employer's balance returned to the exact 1,006,150,725 baseline afterward) plus a soft-deleted `Draft` test row under a throwaway series.
  - Restarted both the port-8000 backend and the port-8501 Streamlit app again to serve this session's changes (each confirmed to be this session's own process, by `CreationDate`/`CommandLine`, before stopping it — not the pre-existing process a real user might have had running).
- **Bug fix (user-reported):** Fixed three issues in `dashboard/views/batch_payments_page.py`: (1) no live employer-balance preview when picking a contract in §2; (2) the §3 drafts table's balance column rendering "messed up"; (3) the §3 table not using the Vazirmatn font. All three traced back to one root cause: the table used `st.dataframe`, which draws every cell on an HTML `<canvas>` — canvas content ignores page CSS entirely (explaining the missing font) and a comma-grouped **Western**-digit number inside an RTL-directed page is prone to Unicode bidi reordering in the browser, which is what "messed up" the balance column. See §2's new "`st.table`, never `st.dataframe`" note for the standing rule this establishes.
  - **Fix 1 (live balance preview):** added `_fetch_employer_balance` (calls the pre-existing `GET /employers/{id}/balance?funding_year=`, untouched by any prior session) and, right after a contract is matched in §2, an `st.info` showing "موجودی فعلی کارفرما تا این لحظه" for that employer at the *currently-set* funding year — read via `st.session_state.get("batch_funding_year", 1402)` since the funding-year widget itself is instantiated later in the script than the search block; Streamlit populates session_state with a widget's current value before the script runs, so this correctly reflects a just-changed funding year too, live, without reordering the page. Because the underlying `calculate_real_balance` already counts `Draft` rows, this preview genuinely reflects "up to this moment," including drafts staged earlier in the same batch.
  - **Fix 2 & 3 (table rendering):** replaced both `st.dataframe` call sites (the §3 drafts table and the finalize "success state" read-only table) with `st.table`, and added the same `table, th, td, .stTable` Vazirmatn/RTL CSS block already used by `dashboard/app.py`'s `render_dashboard()`. Added `_to_persian_digits`/updated `_format_rials` to render on-screen numbers (Rial amounts and the funding-year column) as Persian-digit strings — the same `to_persian_numbers()` convention `dashboard/app.py` already uses — while the Excel export (already raw-numeric, unaffected) and all tracking-code columns (identifiers, not quantities — deliberately left as plain ASCII so they stay copy/paste-matchable against the database) were left untouched.
  - **Verified end-to-end in the live browser, no workarounds needed this time:** the search-box/button-click flakiness documented in the two prior entries did not reproduce this session — searched for a real contract, and the balance preview appeared immediately showing the employer's correct current balance; filled in the row and clicked "Add," and the persistent success message showed the exact correct before/after balances in Persian digits; the §3 table (now a real `<table>` DOM element, itself proof `st.table` is in effect — `st.dataframe`'s canvas content is invisible to `get_page_text`) showed both rows with correctly-ordered, non-scrambled Persian-digit numbers; a direct `getComputedStyle` check on a table cell confirmed `font-family: Vazirmatn, sans-serif`, `direction: rtl`, `text-align: center`. Cleaned up both test payments afterward and confirmed the employer's balance returned to the exact 1,006,150,725 baseline.

---

## Continuous Update Protocol

**Adopted and in effect.** From this point forward, whenever a coding task, bug fix, refactor, or feature implementation is completed in this workspace, a concise entry is appended to §5 (Active Changelog & Action Registry) above — dated, scoped, and noting any follow-up implications — before the response concludes. Sections 1–4 (architecture/business-logic reference) are updated in place, not appended to, whenever the change actually alters that structure (e.g. a new table, a new endpoint, a changed business rule) — the changelog records *that it changed*, the reference sections record *what is currently true*.


## File: Docs\Technical Transition Report_R2.md
------------------------------


# 📂 سند فنی انتقال وضعیت پروژه (Technical Transition Report) \- نسخه R3

نام پروژه: سامانه مالی نظارت بر تأمین اعتبار طرح‌های پژوهشی ساتع (SATE\_Fin\_Dev)  
موقعیت کنونی: اتمام فاز ۴ (فرم‌های ورود اطلاعات) | ورود به فاز دمو، توسعه داشبوردهای تحلیلی و امنیت  
نقش محوری: معماری سیستم، مهندسی داده، و مدیریت محصول (حفظ یکپارچگی مالی)  
سلام\! ما در حال توسعه سامانه جامع مالی ساتع هستیم. هدف این سامانه ایجاد شفافیت مالی، نظارت بر تعهدات قانونی (ماده ۶۵ قانون بودجه) و مدیریت یکپارچه جریان مالی از واریز تا پرداخت است. ما از دیتابیس‌های سنتی (مانند Access که دارای محدودیت است) عبور کرده و یک زیرساخت استاندارد با PostgreSQL بنا کرده‌ایم. لطفاً برای درک کامل وضعیت پروژه، معماری زیر را با دقت تحلیل کنید.

### 🛠 بخش اول: زیرساخت و ساختار کدینگ (Tech Stack & Architecture)

پروژه کاملاً ایزوله در محیط Conda (sate\_env) قرار دارد. ما از معماری چندلایه (Multi-tier Architecture) برای جداسازی منطق کسب‌وکار از لایه نمایش استفاده کرده‌ایم:

* زبان و فریم‌ورک‌ها: Python 3.10+ | Backend: FastAPI | Frontend: Streamlit (RTL Vazirmatn).  
* پایگاه داده: PostgreSQL | ORM: SQLAlchemy 2.0.  
* ساختار دایرکتوری‌ها (Coding Structure):  
  * core/: تنظیمات پایه شامل database.py (کانفیگ کانکشن استخر داده).  
  * models/: مدل‌های دیتابیس شامل کلاس پایه SoftDeleteMixin.  
  * schemas/: اعتبارسنجی داده‌ها (Pydantic Models) برای ورودی و خروجی APIها.  
  * api/v1/: لایه کنترلر شامل routers و فایل‌های endpoints/ (مثل contracts.py).  
  * services/: هسته‌های محاسباتی و منطق تجاری (financial\_engine.py).  
  * dashboard/: کدهای لایه نمایش (Streamlit) شامل app.py و پوشه views/ برای فرم‌ها.  
  * scripts/: فایل‌های مربوط به ETL و استخراج داده اولیه.

### 🗄 بخش دوم: ساختار دیتابیس طراحی‌شده (Database Schema)

دیتابیس کاملاً رابطه‌ای و مبتنی بر حسابداری تعهدی است. تمامی جداول از SoftDeleteMixin ارث‌بری می‌کنند (is\_deleted \= False) تا هیچ رکورد مالی به‌صورت فیزیکی حذف نشود و تاریخچه حفظ گردد.

* مشمولین (employers): شامل نوع مشمول (مادر، زیرمجموعه، مستقل). *ابتکار مهندسی:* استفاده از parent\_code (Self-referencing FK) برای اعمال منطق تجمیع مالی هلدینگ‌ها.  
* تکالیف و واریزها (annual\_mandates & deposit\_receipts): ثبت تعهدات قانونی و واریزی‌های فیزیکی به صندوق.  
* دانشگاه‌ها (universities) و فناوران (researchers): مجریان طرح‌ها با نگاشت یک‌به‌چند (هر فناور متعلق به یک دانشگاه).  
* قراردادها (contracts): جدول مرکزی (Junction). *قانون تجاری:* فقط شرکت‌های "مادر" و "مستقل" اجازه انعقاد قرارداد دارند.  
* پرداختی‌ها (payments): جداسازی payment\_year (خروج پول) از funding\_year (سال منبع تأمین اعتبار). تمامی محاسبات مانده حساب منحصراً بر اساس funding\_year انجام می‌شود تا مشکل پرداخت‌های معوق حل شود.  
* انتقالات اعتباری (credit\_transfers): برای اعمال اصلاحیه تبصره ۲ ماده ۵ (جلوگیری از رسوب منابع بدون مخدوش شدن تاریخچه واریزی‌ها).

### 📥 بخش سوم: استراتژی Import داده‌ها (ETL Pipelines)

با توجه به اینکه داده‌های تاریخی از سال ۱۳۹۸ باید وارد سیستم شوند، فرآیند انتقال داده (ETL) با استفاده از Pandas توسعه یافته است. در زمان Import تمام ارقام پولی اکسل (میلیارد ریال) در $10^9$ ضرب شده و به عنوان "ریال پایه" در تایپ Numeric(18,2) ذخیره می‌شوند.  
چالش فنی در فاز Import: مدیریت رکوردهای تکراری در اجرای مجدد اسکریپت‌ها  
برای این چالش دو راهکار در نظر گرفته شد:

| ویژگی | راهکار الف: Truncate / Drop & Load (استفاده فعلی در MVP) | راهکار ب: Upsert (Insert on Conflict Update) |
| ----: | ----: | ----: |
| مکانیزم | پاک کردن کل جدول با CASCADE و بازنویسی مجدد از فایل اکسل. | جستجوی کلید اصلی، در صورت وجود آپدیت، در غیر این صورت درج. |
| مزایا | \- سرعت توسعه بسیار بالا. \- اطمینان از پاک شدن داده‌های کثیف (Dirty Data) قبلی. | \- حفظ کامل رکوردهایی که توسط کاربران از طریق فرم‌ها (UI) ثبت شده‌اند. |
| معایب | \- پاک شدن داده‌های جدیدی که از طریق سیستم وارد شده‌اند (نامناسب برای Production). | \- نیازمند کدنویسی پیچیده‌تر در SQLAlchemy. \- کندتر بودن فرآیند Import اولیه. |
| تصمیم معماری | برای فاز *توسعه اولیه* مناسب بود، اما با راه‌اندازی فرم‌های ورود اطلاعات (فاز ۴)، باید ممنوع شود. از این پس فقط از راهکار Upsert یا درج دستی استفاده خواهد شد. |  |

### ⚙️ بخش چهارم: هسته‌های محاسباتی و منطق تجاری (Business Logic Cores)

قلب تپنده سامانه در پوشه services/ قرار دارد. هسته‌های محاسباتی فعلی و در حال توسعه عبارتند از:

1. هسته ترازنامه (Real-time Balance Calculator): محاسبه پویای مانده حساب کارفرما با فرمول: *(مجموع واریزی مادر و زیرمجموعه‌ها در سال X) \- (مجموع هزینه‌کرد مادر در سال X)*.  
2. هسته مدیریت همزمانی تراکنش‌ها (Concurrency Core): هنگام ثبت پرداخت، برای جلوگیری از Race Conditions، از قفل‌گذاری بدبینانه (.with\_for\_update()) روی رکورد قرارداد استفاده شده است. سامانه در صورت منفی شدن مانده حساب، صرفاً "هشدار" می‌دهد و جلوی ثبت را نمی‌گیرد (جلوگیری از تغییر خودسرانه منطق مالی MVP).  
3. هسته طبقه‌بندی پویای قراردادها: قراردادها به صورت Real-time با استفاده از کوئری‌های SQL به سه دسته "فعال"، "خاتمه‌یافته" و "راکد" تقسیم می‌شوند.  
4. *(نیازمند توسعه)* هسته پردازش شبکه همکاری (Collaboration Network Engine): یک موتور محاسباتی گراف‌محور برای کشف ارتباطات بین "کارفرمایان" و "دانشگاه‌های مجری" جهت تغذیه داشبوردهای تعاملی.

### 📊 بخش پنجم: داشبوردهای مدیریتی و تحلیلی (BI Dashboards)

وضعیت فعلی: تب‌های اولیه برای ترازنامه اختصاصی مشمولین و نمای کلان کشور (نمودارهای Waterfall) ایجاد شده است. تکمیل داشبوردها (پروپوزال مدیر محصول): برای دستیابی به اهداف نظارتی، توسعه داشبوردهای زیر در اولویت قرار دارد:

* داشبورد عملکرد مشمولین (Employer KPI): بررسی درصد تحقق واریز (واریزی/تکلیفی) و نمایش دستگاه‌های متخلف (Red Flags).  
* داشبورد رتبه‌بندی و سهم‌بازار دانشگاه‌ها: استفاده از نمودار *Sankey Diagram* برای نمایش جریان پول از هلدینگ‌ها به سمت دانشگاه‌های خاص و رتبه‌بندی دانشگاه‌های موفق در جذب بودجه پژوهشی.  
* داشبورد شبکه تعاملات (Heatmap/Network): ماتریس همکاری کارفرما-مجری برای شناسایی قطب‌های پژوهشی پرتکرار.  
* داشبورد قراردادهای رسوب‌کرده (Stagnant Alerts): لیستی از قراردادهایی که بیش از ۲ سال (از ۱۴۰۲) دریافتی نداشته‌اند جهت اعمال اصلاحیه تبصره ۲ ماده ۵.

### 🚀 بخش ششم: نقشه راه و اقدامات باقیمانده (Roadmap)

اقدامات زیر به ترتیب اولویت برای ادامه توسعه سیستم تعریف شده‌اند:

1. گام فوری (جهت جلسه دمو): استقرار موقت با تونل‌زنی. استفاده از Ngrok یا Cloudflare Tunnels برای ایجاد دسترسی عمومی موقت (بدون نیاز به دیپلویمنت سرور) جهت نمایش دمو به کارفرما.  
2. فاز ۳: تکمیل داشبوردهای تحلیلی ذکر شده در بخش پنجم (GIS، رتبه‌بندی، شبکه همکاری).  
3. فاز ۵ (IAM & Security): پیاده‌سازی سیستم Authentication (بر مبنای JWT) و Role-Based Access Control (RBAC) برای نقش‌های: ادمین، کارشناس مالی، مدیر و کارشناس پاسخگویی (هر نقش فقط داده‌های مجاز خود را ببیند).  
4. فاز ۶ (Deployment): داکرایز کردن (Dockerizing) دیتابیس و اپلیکیشن (FastAPI \+ Streamlit)، تنظیم Nginx، و استقرار دائم روی سرور ابری لینوکسی بومی (جهت حفظ امنیت داده‌های مالی و کدهای ملی).

پایان گزارش.  


## File: models\contract.py
------------------------------
from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Text

from core.database import Base
from models.employer import SoftDeleteMixin


class Contract(SoftDeleteMixin, Base):
    """Represent a research contract registered in the financial system."""

    __tablename__ = "contracts"

    tracking_code = Column(String(50), primary_key=True)
    employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code"),
        nullable=False,
    )
    university_id = Column(
        String(20),
        ForeignKey("universities.national_id"),
        nullable=False,
    )
    researcher_id = Column(
        String(10),
        ForeignKey("researchers.national_code"),
        nullable=False,
    )
    proposal_id = Column(String(50), nullable=True)
    contract_number = Column(String(100), nullable=True)
    attachment_path = Column(String(255), nullable=True)
    contract_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(22, 0), nullable=False)
    title = Column(Text, nullable=False)
    duration_months = Column(Integer, nullable=True)
    status = Column(String(50), default="Active")


## File: models\deposits.py
------------------------------
"""Deposit (نظارت بر واریز) models for the SATE financial system.

This module defines the domain models used to monitor mandated budgets and the
deposits actually received from each employer.

Tables
------
Deposit
    Spec-defined aggregate record tying the mandated amount and the deposited
    amount for a given employer and fiscal year. Enforces a composite unique
    constraint on ``(employer_code, fiscal_year)`` so that there is exactly one
    mandate/deposit summary per employer-year pair.
AnnualMandate
    Master record of the mandated budget amount per employer per fiscal year.
DepositReceipt
    Detail record of an individual deposit receipt per employer per fiscal year.
"""

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from core.database import Base, SoftDeleteMixin


class Deposit(SoftDeleteMixin, Base):
    """Aggregate mandate-vs-deposit summary for one employer in one fiscal year.

    Attributes
    ----------
    id : int
        Auto-incrementing surrogate primary key.
    employer_code : str
        Foreign key to ``employers.classification_code``.
    fiscal_year : int
        Fiscal (Persian-calendar) year the record applies to.
    mandated_amount : Decimal
        Amount mandated for the employer in the given year.
    deposit_amount : Decimal
        Amount actually deposited by the employer in the given year.
    deposit_date : date or None
        Date the deposit was made, when known.
    receipt_number : str or None
        Reference number of the deposit receipt, when available.

    Notes
    -----
    A composite unique constraint on ``(employer_code, fiscal_year)`` guarantees
    a single summary row per employer-year combination.
    """

    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_year = Column(Integer, nullable=False, index=True)
    mandated_amount = Column(Numeric(18, 2), nullable=False)
    deposit_amount = Column(Numeric(18, 2), nullable=False)
    deposit_date = Column(Date, nullable=True)
    receipt_number = Column(String(50), nullable=True)

    employer = relationship("Employer", backref="deposits")

    __table_args__ = (
        UniqueConstraint("employer_code", "fiscal_year", name="uq_deposit_employer_year"),
    )

    def __repr__(self):
        return (
            f"<Deposit(employer={self.employer_code}, year={self.fiscal_year}, "
            f"mandated={self.mandated_amount}, deposited={self.deposit_amount})>"
        )


class AnnualMandate(SoftDeleteMixin, Base):
    """Master record tracking mandated budget amounts per employer per fiscal year."""

    __tablename__ = "annual_mandates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_year = Column(Integer, nullable=False, index=True)
    mandated_amount = Column(Numeric(22, 0), nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("employer_code", "fiscal_year", name="uq_employer_year_mandate"),
    )

    def __repr__(self):
        return f"<AnnualMandate(employer={self.employer_code}, year={self.fiscal_year}, amount={self.mandated_amount})>"


class DepositReceipt(SoftDeleteMixin, Base):
    """Detail record tracking individual deposit receipts per employer per fiscal year."""

    __tablename__ = "deposit_receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fiscal_year = Column(Integer, nullable=False, index=True)
    deposit_amount = Column(Numeric(22, 0), nullable=False)
    deposit_date = Column(Date, nullable=True)
    receipt_number = Column(String(50), nullable=True)
    attachment_path = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<DepositReceipt(employer={self.employer_code}, year={self.fiscal_year}, amount={self.deposit_amount})>"


## File: models\employer.py
------------------------------
"""Employer (مشمولین) model for the SATE financial system.

Represents organizations subject to research-and-technology funding mandates.
An employer may be a Mother company, a Subsidiary of another employer, or an
Independent entity. The ``parent_code`` foreign key is self-referential,
allowing hierarchical grouping of subsidiary employers under their parent.
"""

from sqlalchemy import CheckConstraint, Column, ForeignKey, String

from core.database import Base, SoftDeleteMixin


class Employer(SoftDeleteMixin, Base):
    """Organization liable for mandated research-and-technology funding.

    Attributes
    ----------
    classification_code : str
        Unique classification code; primary key (max 20 chars).
    name : str
        Official name of the employer (max 200 chars).
    employer_type : str
        Structural type: one of ``Mother``, ``Subsidiary`` or ``Independent``.
    parent_code : str or None
        Classification code of the parent (mother) employer. Self-referential
        foreign key to ``employers.classification_code``; ``None`` for mother
        or independent employers.
    province : str
        Province where the employer is located (max 50 chars).
    affairs_category : str or None
        Optional functional category of the employer's affairs.
    upper_organization : str
        Name of the supervising/executing body above this employer.
    status : str
        Lifecycle status; defaults to ``Active``.
    """

    __tablename__ = "employers"

    classification_code = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    employer_type = Column(String(20), nullable=False)
    parent_code = Column(
        String(20),
        ForeignKey("employers.classification_code"),
        nullable=True,
    )
    province = Column(String(50), nullable=False)
    affairs_category = Column(String(100), nullable=True)
    upper_organization = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="Active")

    __table_args__ = (
        CheckConstraint(
            "employer_type IN ('Mother', 'Subsidiary', 'Independent')",
            name="check_employer_type",
        ),
        CheckConstraint(
            "status IN ('Active', 'Inactive')",
            name="check_employer_status",
        ),
    )

    def __repr__(self):
        return (
            f"<Employer(code={self.classification_code!r}, "
            f"name={self.name!r}, type={self.employer_type!r})>"
        )


## File: models\payment.py
------------------------------
"""Payment (پرداختی‌ها) model for the SATE financial system.

Records individual disbursements made against a research contract. Each payment
references its parent contract via ``contract_tracking_code`` and captures the
amount, date, execution year and payment type.
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String

from core.database import Base, SoftDeleteMixin


class Payment(SoftDeleteMixin, Base):
    """A single payment made against a research contract.

    Attributes
    ----------
    tracking_code : str
        Unique tracking code for the payment; primary key (max 50 chars).
    contract_tracking_code : str
        Foreign key to ``contracts.tracking_code``.
    amount : Decimal
        Payment amount (Numeric(18, 2)).
    payment_date : date
        Date the payment was executed.
    execution_year : int
        Fiscal (execution) year the payment is recorded against.
    payment_type : str
        Category/type of the payment (max 50 chars).
    series : str or None
        Optional series/sequence identifier.
    notification_letter_number : str or None
        Optional notification letter reference number.
    notification_date : date or None
        Optional date of the notification letter.
    payment_year : int or None
        Cash-flow year of the payment (legacy/compatibility field).
    funding_year : int or None
        Budget-consumption year of the payment (legacy/compatibility field).
    attachment_path : str or None
        Optional path to a supporting attachment.
    status : str
        Lifecycle status; ``"Draft"`` while staged in the batch-payment
        cart (reserves funds against the employer's balance without being
        a finalized disbursement) or ``"Final"`` once confirmed. Defaults
        to ``"Final"`` so directly-inserted payments (e.g. bulk ETL
        imports) behave as before this field existed.
    """

    __tablename__ = "payments"

    tracking_code = Column(String(50), primary_key=True)
    contract_tracking_code = Column(
        String(50),
        ForeignKey("contracts.tracking_code"),
        nullable=False,
    )
    amount = Column(Numeric(18, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    execution_year = Column(Integer, nullable=False)
    payment_type = Column(String(50), nullable=False)

    series = Column(String(50), nullable=True)
    notification_letter_number = Column(String(100), nullable=True)
    notification_date = Column(Date, nullable=True)
    payment_year = Column(Integer, nullable=True)
    funding_year = Column(Integer, nullable=True)
    attachment_path = Column(String(255), nullable=True)
    status = Column(String(20), default="Final")

    def __repr__(self):
        return (
            f"<Payment(tracking_code={self.tracking_code!r}, "
            f"contract={self.contract_tracking_code!r}, amount={self.amount})>"
        )


## File: models\researchers.py
------------------------------
"""Researcher (فناور) model for the SATE financial system.

Represents an individual researcher/technologist who is affiliated with a
university and may participate in one or more research contracts.
"""

from sqlalchemy import Column, ForeignKey, String

from core.database import Base, SoftDeleteMixin


class Researcher(SoftDeleteMixin, Base):
    """A researcher (فناور) affiliated with a university.

    Attributes
    ----------
    national_code : str
        Iranian national code; primary key (max 10 chars).
    tracking_code : str or None
        Optional tracking code assigned to the researcher.
    first_name : str
        Researcher's first name (max 100 chars).
    last_name : str
        Researcher's last name (max 100 chars).
    full_name : str
        Full display name of the researcher (max 200 chars).
    mobile : str or None
        Contact mobile number.
    email : str or None
        Contact email address.
    academic_rank : str or None
        Academic rank/position (max 50 chars).
    university_id : str
        Foreign key to ``universities.national_id``.
    education_level : str or None
        Highest education level attained.
    researcher_type : str or None
        Category/type of researcher.
    status : str
        Lifecycle status; defaults to ``Active``.
    """

    __tablename__ = "researchers"

    national_code = Column(String(10), primary_key=True)
    tracking_code = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    mobile = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    academic_rank = Column(String(50), nullable=True)
    university_id = Column(
        String(20),
        ForeignKey("universities.national_id"),
        nullable=False,
    )
    education_level = Column(String(50), nullable=True)
    researcher_type = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="Active")

    def __repr__(self):
        return f"<Researcher(national_code={self.national_code!r}, full_name={self.full_name!r})>"


## File: models\transfer.py
------------------------------
"""Credit Transfer model for the SATE financial system.

Junction table allocating unspent funds from one employer to a specific
contract, typically routed through the central Secretariat, without altering
the core deposit/payment tables.
"""

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from core.database import Base, SoftDeleteMixin


class CreditTransfer(SoftDeleteMixin, Base):
    """Track fund transfers between employers.

    Allows allocation of unspent funds from various employers to contracts
    managed by a central Secretariat without altering the core deposit/payment
    tables.

    Attributes
    ----------
    id : int
        Auto-incrementing surrogate primary key.
    source_employer_code : str
        Employer the funds originate from (FK to ``employers.classification_code``).
    destination_employer_code : str
        Employer the funds are transferred to (FK to ``employers``); defaults to
        the Secretariat.
    broker_name : str or None
        Optional broker facilitating the transfer.
    fiscal_year : int
        Fiscal year the transferred funds originated from.
    amount : Decimal
        Transfer amount in Rials.
    contract_tracking_code : str
        Contract receiving the transferred funds (FK to ``contracts.tracking_code``).
    documentation : str or None
        Supporting documentation or free-text notes.
    """

    __tablename__ = "credit_transfers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    source_employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code"),
        nullable=False,
        index=True,
    )

    destination_employer_code = Column(
        String(20),
        ForeignKey("employers.classification_code"),
        nullable=False,
        default="128342",
        index=True,
    )

    broker_name = Column(String(100), nullable=True)

    fiscal_year = Column(Integer, nullable=False, index=True)

    amount = Column(Numeric(22, 0), nullable=False)

    contract_tracking_code = Column(
        String(50),
        ForeignKey("contracts.tracking_code"),
        nullable=False,
        index=True,
    )

    contract = relationship("Contract", backref="credit_transfers")

    documentation = Column(Text, nullable=True)

    def __repr__(self):
        return (
            f"<CreditTransfer(id={self.id}, from={self.source_employer_code}, "
            f"to={self.destination_employer_code}, amount={self.amount}, "
            f"year={self.fiscal_year})>"
        )


## File: models\university.py
------------------------------
"""University (دانشگاه‌ها) model for the SATE financial system.

Represents a university or executing institution that supervises researchers
and administers research contracts on behalf of the funding program.
"""

from sqlalchemy import Column, String, Text

from core.database import Base, SoftDeleteMixin


class University(SoftDeleteMixin, Base):
    """University or executing institution.

    Attributes
    ----------
    national_id : str
        National identifier of the institution; primary key (max 20 chars).
    tracking_code : str or None
        Optional tracking code assigned to the institution.
    name : str
        Official name of the institution (max 200 chars).
    city : str or None
        City where the institution is located.
    address : str or None
        Postal address of the institution.
    province : str
        Province where the institution is located (max 50 chars).
    university_type : str
        Category/type of the institution (max 50 chars).
    status : str
        Lifecycle status; defaults to ``Active``.
    """

    __tablename__ = "universities"

    national_id = Column(String(20), primary_key=True, comment="شناسه ملی موسسه")
    tracking_code = Column(String(50), nullable=True, comment="کد رهگیری")
    name = Column(String(200), nullable=False, comment="نام موسسه")
    city = Column(String(100), nullable=True, comment="شهر")
    address = Column(Text, nullable=True, comment="آدرس")
    province = Column(String(50), nullable=False, comment="استان موسسه")
    university_type = Column(String(50), nullable=False, comment="نوع موسسه")
    status = Column(String(20), nullable=False, default="Active", comment="وضعیت")

    def __repr__(self):
        return f"<University(national_id={self.national_id!r}, name={self.name!r})>"


## File: schemas\contract_schema.py
------------------------------
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ContractSearchResult(BaseModel):
    """Represent one active contract returned to API consumers."""

    contract_tracking_code: str = Field(
        ..., description="The contract tracking code"
    )
    title: str = Field(..., description="The contract title")
    employer_name: Optional[str] = Field(
        None, description="Name of the linked employer"
    )
    employer_classification_code: Optional[str] = Field(
        None, description="Classification code of the linked employer"
    )
    university_name: Optional[str] = Field(
        None, description="Name of the executing university"
    )
    researcher_name: Optional[str] = Field(
        None, description="Full name of the researcher"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "contract_tracking_code": "CNT-1403-001",
                "title": "پروژه پژوهشی نمونه",
                "employer_name": "وزارت نمونه",
                "employer_classification_code": "EMP001",
                "university_name": "دانشگاه نمونه",
                "researcher_name": "علی رضایی",
            }
        }


class ContractCreate(BaseModel):
    """Define the payload accepted when registering a new contract.

    Field length limits mirror the ``contracts`` table column definitions so
    that oversized input is rejected with a clear 422 validation error instead
    of silently failing as a database ``DataError`` at insert time.
    """

    tracking_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="The contract tracking code (primary key)",
    )
    employer_classification_code: str = Field(
        ...,
        max_length=20,
        description="Classification code of the contracting employer",
    )
    university_national_id: str = Field(
        ...,
        max_length=20,
        description="National ID of the executing university",
    )
    researcher_national_id: str = Field(
        ...,
        max_length=10,
        description="National code of the lead researcher",
    )
    contract_number: Optional[str] = Field(
        None, description="Operational contract number"
    )
    proposal_id: Optional[str] = Field(
        None, max_length=50, description="Identifier of the linked proposal"
    )
    attachment_path: Optional[str] = Field(
        None, description="Local path of the archived contract document"
    )
    title: str = Field(
        ..., min_length=1, description="Contract or project title"
    )
    total_amount: int = Field(
        ...,
        gt=0,
        description=(
            "Total contract amount in whole Rials. Integer to match the "
            "database's zero-decimal Numeric(22, 0) column and reject "
            "fractional amounts instead of silently truncating them."
        ),
    )
    contract_date: date = Field(
        ..., description="Contract date in Gregorian ISO format"
    )
    duration_months: int = Field(
        ..., gt=0, description="Contract duration in months"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "CNT-1403-002",
                "employer_classification_code": "EMP001",
                "university_national_id": "UNI001",
                "researcher_national_id": "1234567890",
                "contract_number": "1403/CON/002",
                "proposal_id": "PRP-1403-002",
                "attachment_path": "data/Archive/Contracts/example.pdf",
                "title": "پروژه تحقیقاتی نمونه",
                "total_amount": 1000000000,
                "contract_date": "2024-03-20",
                "duration_months": 12,
            }
        }


class ContractUpdate(BaseModel):
    """Define the payload accepted when updating an existing contract.

    Mirrors :class:`ContractCreate` except ``tracking_code`` is omitted —
    the primary key is supplied via the URL path and is never changed by an
    update. Field length limits mirror the ``contracts`` table column
    definitions for the same reason as :class:`ContractCreate`.
    """

    employer_classification_code: str = Field(
        ...,
        max_length=20,
        description="Classification code of the contracting employer",
    )
    university_national_id: str = Field(
        ...,
        max_length=20,
        description="National ID of the executing university",
    )
    researcher_national_id: str = Field(
        ...,
        max_length=10,
        description="National code of the lead researcher",
    )
    contract_number: Optional[str] = Field(
        None, description="Operational contract number"
    )
    proposal_id: Optional[str] = Field(
        None, max_length=50, description="Identifier of the linked proposal"
    )
    attachment_path: Optional[str] = Field(
        None, description="Local path of the archived contract document"
    )
    title: str = Field(
        ..., min_length=1, description="Contract or project title"
    )
    total_amount: int = Field(
        ...,
        gt=0,
        description=(
            "Total contract amount in whole Rials. Integer to match the "
            "database's zero-decimal Numeric(22, 0) column and reject "
            "fractional amounts instead of silently truncating them."
        ),
    )
    contract_date: date = Field(
        ..., description="Contract date in Gregorian ISO format"
    )
    duration_months: int = Field(
        ..., gt=0, description="Contract duration in months"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "employer_classification_code": "EMP001",
                "university_national_id": "UNI001",
                "researcher_national_id": "1234567890",
                "contract_number": "1403/CON/002",
                "proposal_id": "PRP-1403-002",
                "attachment_path": "data/Archive/Contracts/example.pdf",
                "title": "پروژه تحقیقاتی نمونه (ویرایش‌شده)",
                "total_amount": 1200000000,
                "contract_date": "2024-03-20",
                "duration_months": 12,
            }
        }


class ContractDetail(BaseModel):
    """Full contract record returned to populate the edit form.

    Unlike :class:`ContractSearchResult` (which carries display names for
    auto-fill confirmation), this exposes the raw foreign-key codes so the
    frontend can pre-select the correct option in each dropdown.
    """

    tracking_code: str = Field(..., description="The contract tracking code")
    employer_classification_code: str = Field(
        ..., description="Classification code of the contracting employer"
    )
    university_national_id: str = Field(
        ..., description="National ID of the executing university"
    )
    researcher_national_id: str = Field(
        ..., description="National code of the lead researcher"
    )
    contract_number: Optional[str] = Field(
        None, description="Operational contract number"
    )
    proposal_id: Optional[str] = Field(
        None, description="Identifier of the linked proposal"
    )
    attachment_path: Optional[str] = Field(
        None, description="Local path of the archived contract document"
    )
    title: str = Field(..., description="Contract or project title")
    total_amount: int = Field(..., description="Total contract amount in whole Rials")
    contract_date: Optional[date] = Field(
        None, description="Contract date in Gregorian ISO format"
    )
    duration_months: Optional[int] = Field(
        None, description="Contract duration in months"
    )
    status: str = Field(..., description="Current contract status")

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "CNT-1403-002",
                "employer_classification_code": "EMP001",
                "university_national_id": "UNI001",
                "researcher_national_id": "1234567890",
                "contract_number": "1403/CON/002",
                "proposal_id": "PRP-1403-002",
                "attachment_path": "data/Archive/Contracts/example.pdf",
                "title": "پروژه تحقیقاتی نمونه",
                "total_amount": 1000000000,
                "contract_date": "2024-03-20",
                "duration_months": 12,
                "status": "فعال",
            }
        }


## File: schemas\employer_schema.py
------------------------------
from pydantic import BaseModel, Field
from datetime import datetime
import jdatetime


class BalanceResponse(BaseModel):
    """
    Response schema for employer balance inquiry.

    Balance formula: (Total Deposits + Transfers In) - (Total Payments + Transfers Out)
    """
    employer_code: str = Field(..., description="The employer's classification code")
    funding_year: int = Field(..., description="The funding year (fiscal year) for the balance calculation")
    total_balance: float = Field(
        ...,
        description=(
            "The calculated real balance: "
            "(Total Deposits + Transfers In) - (Total Payments + Transfers Out)"
        ),
    )
    inquiry_date_jalali: str = Field(..., description="Current date in Persian/Jalali calendar format")

    class Config:
        json_schema_extra = {
            "example": {
                "employer_code": "EMP001",
                "funding_year": 1403,
                "total_balance": 125000000.50,
                "inquiry_date_jalali": "1403/03/30"
            }
        }

    @staticmethod
    def get_current_jalali_date() -> str:
        """
        Returns the current date in Jalali (Persian) calendar format.
        Format: YYYY/MM/DD
        """
        now = jdatetime.datetime.now()
        return now.strftime("%Y/%m/%d")


## File: schemas\payment_schema.py
------------------------------
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class PaymentValidationRequest(BaseModel):
    """
    Request schema for validating a payment before registration.
    """
    contract_tracking_code: str = Field(..., description="The contract tracking code linked to the payment")
    amount: float = Field(..., description="The payment amount to be validated", gt=0)
    funding_year: int = Field(..., description="The funding year for the payment", ge=1300, le=1500)

    class Config:
        json_schema_extra = {
            "example": {
                "contract_tracking_code": "CNT-1403-001",
                "amount": 50000000.0,
                "funding_year": 1403
            }
        }


class PaymentValidationResponse(BaseModel):
    """
    Response schema for payment validation results.
    """
    employer_code: str = Field(..., description="The employer classification code")
    current_balance: float = Field(..., description="Current balance before the payment")
    payment_amount: float = Field(..., description="The payment amount being validated")
    new_balance: float = Field(..., description="Projected balance after the payment")
    is_negative: bool = Field(..., description="Whether the new balance will be negative")
    warning_message: Optional[str] = Field(None, description="Warning message if balance becomes negative")

    class Config:
        json_schema_extra = {
            "example": {
                "employer_code": "EMP001",
                "current_balance": 125000000.0,
                "payment_amount": 50000000.0,
                "new_balance": 75000000.0,
                "is_negative": False,
                "warning_message": None
            }
        }


class PaymentDraftCreate(BaseModel):
    """
    Request schema for staging one payment as a database-backed draft.

    A draft immediately reserves its ``amount`` against the linked
    employer's real balance (``calculate_real_balance`` sums ``Draft`` and
    ``Final`` payments alike) — insufficient funds reject the request with
    HTTP 400 rather than allowing an over-committed draft to be staged.
    """
    tracking_code: str = Field(..., description="Unique payment tracking code")
    contract_tracking_code: str = Field(..., description="Contract tracking code linked to the payment")
    amount: float = Field(..., description="Payment amount in base Rials", gt=0)
    funding_year: int = Field(..., description="Budget consumption (balance-reserving) year", ge=1300, le=1500)
    payment_year: Optional[int] = Field(default=None, description="Cash flow year", ge=1300, le=1500)
    series: Optional[str] = Field(default=None, description="Payment series/batch identifier")
    notification_letter_number: Optional[str] = Field(
        default=None, description="Notification letter number"
    )
    notification_date: Optional[date] = Field(default=None, description="Notification date")

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "PAY-1403-0001",
                "contract_tracking_code": "CNT-1403-001",
                "amount": 50000000.0,
                "funding_year": 1403,
                "payment_year": 1403,
                "series": "15",
                "notification_letter_number": None,
                "notification_date": None,
            }
        }


class PaymentDraftResponse(BaseModel):
    """
    Response schema representing one payment draft (or a finalized payment).

    Carries the linked contract's title/amount, employer name, and
    university name alongside the raw codes, so the frontend drafts table
    can display and export a fully readable row without a second lookup
    round-trip per row.
    """
    tracking_code: str = Field(..., description="Unique payment tracking code")
    contract_tracking_code: str = Field(..., description="Contract tracking code linked to the payment")
    contract_title: Optional[str] = Field(None, description="Title of the linked contract")
    contract_total_amount: Optional[float] = Field(
        None, description="Total amount of the linked contract, in base Rials"
    )
    employer_code: Optional[str] = Field(None, description="Classification code of the linked employer")
    employer_name: Optional[str] = Field(None, description="Name of the linked employer")
    university_name: Optional[str] = Field(
        None, description="Name of the university/institution executing the contract"
    )
    amount: float = Field(..., description="Payment amount in base Rials")
    funding_year: int = Field(..., description="Budget consumption (balance-reserving) year")
    payment_year: Optional[int] = Field(None, description="Cash flow year")
    series: Optional[str] = Field(None, description="Payment series/batch identifier")
    status: str = Field(..., description="'Draft' or 'Final'")
    employer_balance_after: Optional[float] = Field(
        None,
        description=(
            "Employer's real balance immediately after this payment, "
            "computed in sequence with any other listed drafts for the "
            "same employer/funding_year"
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "PAY-1403-0001",
                "contract_tracking_code": "CNT-1403-001",
                "contract_title": "پروژه پژوهشی نمونه",
                "contract_total_amount": 1000000000.0,
                "employer_code": "EMP001",
                "employer_name": "وزارت نمونه",
                "university_name": "دانشگاه نمونه",
                "amount": 50000000.0,
                "funding_year": 1403,
                "payment_year": 1403,
                "series": "15",
                "status": "Draft",
                "employer_balance_after": 75000000.0,
            }
        }


class PaymentDraftCreateResponse(PaymentDraftResponse):
    """
    Response schema returned after successfully creating one draft.

    Extends :class:`PaymentDraftResponse` with the employer's balance
    immediately *before* this payment, so the frontend can show a full
    before/after transition without a separate API call.
    """
    employer_balance_before: float = Field(
        ..., description="Employer's real balance immediately before this payment"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "PAY-1403-0001",
                "contract_tracking_code": "CNT-1403-001",
                "contract_title": "پروژه پژوهشی نمونه",
                "contract_total_amount": 1000000000.0,
                "employer_code": "EMP001",
                "employer_name": "وزارت نمونه",
                "university_name": "دانشگاه نمونه",
                "amount": 50000000.0,
                "funding_year": 1403,
                "payment_year": 1403,
                "series": "15",
                "status": "Draft",
                "employer_balance_before": 125000000.0,
                "employer_balance_after": 75000000.0,
            }
        }


class DraftDeleteResponse(BaseModel):
    """Response schema confirming a draft was removed."""
    message: str = Field(..., description="Human readable confirmation message")
    tracking_code: str = Field(..., description="Tracking code of the removed draft")


class FinalizeBatchRequest(BaseModel):
    """Request schema for finalizing every draft in a given series."""
    series: str = Field(..., min_length=1, description="Payment series/batch identifier to finalize")

    class Config:
        json_schema_extra = {"example": {"series": "15"}}


class FinalizeBatchResponse(BaseModel):
    """Response schema returned after finalizing a batch."""
    message: str = Field(..., description="Human readable success message")
    series: str = Field(..., description="Payment series/batch identifier that was finalized")
    finalized_count: int = Field(..., description="Number of drafts moved to 'Final' status")
    finalized_payments: List[PaymentDraftResponse] = Field(
        default_factory=list,
        description="The full enriched records that were finalized, for client-side reporting/export",
    )


## File: schemas\researcher_schema.py
------------------------------
from typing import Optional

from pydantic import BaseModel, Field


class ResearcherCreate(BaseModel):
    """Payload for registering a new researcher (فناور), aligned to models/researchers.py."""
    national_code: str = Field(..., min_length=10, max_length=10, description="National code of the researcher (10 digits)")
    first_name: str = Field(..., description="First name of the researcher")
    last_name: str = Field(..., description="Last name of the researcher")
    mobile: Optional[str] = Field(None, description="Mobile phone number")
    email: Optional[str] = Field(None, description="Email address")
    academic_rank: Optional[str] = Field(None, description="Academic rank")
    education_level: Optional[str] = Field(None, description="Education level")
    researcher_type: Optional[str] = Field(None, description="Researcher type")
    university_id: str = Field(..., description="National ID of the affiliated university/institution")
    status: str = Field("Active", description="Status: 'Active' or 'Inactive'")

    class Config:
        json_schema_extra = {
            "example": {
                "national_code": "1234567890",
                "first_name": "علی",
                "last_name": "رضایی",
                "mobile": "09123456789",
                "email": "ali@example.com",
                "academic_rank": "استادیار",
                "education_level": "دکتری",
                "researcher_type": "هیات علمی",
                "university_id": "14001234567",
                "status": "Active",
            }
        }


class ResearcherCreated(BaseModel):
    """Confirmation returned after a researcher is created."""
    national_code: str
    full_name: str
    university_id: str
    academic_rank: Optional[str] = None
    education_level: Optional[str] = None
    researcher_type: Optional[str] = None
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "national_code": "1234567890",
                "full_name": "علی رضایی",
                "university_id": "14001234567",
                "academic_rank": "استادیار",
                "education_level": "دکتری",
                "researcher_type": "هیات علمی",
                "status": "Active",
            }
        }


## File: schemas\university_schema.py
------------------------------
from typing import Optional

from pydantic import BaseModel, Field


class UniversityCreate(BaseModel):
    """Payload for registering a new university / executing institution."""
    national_id: str = Field(..., min_length=1, max_length=20, description="National ID of the institution")
    name: str = Field(..., description="Full name of the institution")
    province: str = Field(..., description="Province where the institution is located")
    university_type: str = Field(..., description="Type of the institution")
    is_active: bool = Field(True, description="Active status (True = Active, False = Inactive)")

    class Config:
        json_schema_extra = {
            "example": {
                "national_id": "14001234567",
                "name": "دانشگاه نمونه",
                "province": "تهران",
                "university_type": "دانشگاه دولتی",
                "is_active": True,
            }
        }


class UniversityCreated(BaseModel):
    """Confirmation returned after a university is created."""
    national_id: str
    name: str
    province: str
    university_type: str
    status: str

    class Config:
        json_schema_extra = {
            "example": {
                "national_id": "14001234567",
                "name": "دانشگاه نمونه",
                "province": "تهران",
                "university_type": "دانشگاه دولتی",
                "status": "Active",
            }
        }


## File: schemas\__init__.py
------------------------------


## File: scripts\add_contract_attachment_path.py
------------------------------
"""Add contract attachment storage to an existing PostgreSQL database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from core.database import engine


def add_contract_attachment_path() -> None:
    """Add the nullable attachment path column idempotently."""
    statement = text(
        """
        ALTER TABLE contracts
        ADD COLUMN IF NOT EXISTS attachment_path VARCHAR(255) NULL
        """
    )
    with engine.begin() as connection:
        connection.execute(statement)


if __name__ == "__main__":
    add_contract_attachment_path()
    print("Contract attachment_path column is ready.")


## File: scripts\add_payment_missing_columns.py
------------------------------
"""Add missing payment tracking columns to an existing PostgreSQL database.

``models/payment.py`` declares ``payment_date``, ``execution_year``, and
``payment_type`` as ``nullable=False``, but the live ``payments`` table
predates those columns entirely (discovered while running
``scripts/import_payments_upsert.py`` against the local dev database).

This migration adds the three columns as **nullable**, not ``NOT NULL``:
1,277 of the table's 1,420 existing rows have no ``notification_date`` (the
column any real ``payment_date`` would be derived from for historical
data), so retroactively enforcing ``NOT NULL`` here would require either
fabricating placeholder dates for most of the table's history or blocking
the migration outright — neither is this script's call to make. Every row
written going forward by ``import_payments_upsert.py`` always supplies all
three columns, so the application-level guarantee holds for new data
without requiring a database-level constraint that legacy rows can't meet
yet. Promoting these columns to ``NOT NULL`` (matching the model exactly)
is a deliberate follow-up decision once a backfill strategy for the 1,277
historical rows is chosen.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from core.database import engine


def add_payment_missing_columns() -> None:
    """Add the nullable payment_date/execution_year/payment_type columns."""
    statement = text(
        """
        ALTER TABLE payments
        ADD COLUMN IF NOT EXISTS payment_date DATE NULL,
        ADD COLUMN IF NOT EXISTS execution_year INTEGER NULL,
        ADD COLUMN IF NOT EXISTS payment_type VARCHAR(50) NULL
        """
    )
    with engine.begin() as connection:
        connection.execute(statement)


if __name__ == "__main__":
    add_payment_missing_columns()
    print("payment_date, execution_year, and payment_type columns are ready.")


## File: scripts\add_payment_status_column.py
------------------------------
"""Add the payment lifecycle status column to an existing PostgreSQL database.

``models/payment.py`` now declares ``status`` (``"Draft"`` while staged in
the batch-payment cart, ``"Final"`` once confirmed — see
``api/v1/endpoints/payments.py``'s draft/finalize-batch endpoints). This
migration adds the column idempotently, defaulting existing and
future-unset rows to ``"Final"`` so every payment written before this
column existed is treated as already confirmed, matching its prior
behavior exactly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from core.database import engine


def add_payment_status_column() -> None:
    """Add the nullable, default-'Final' status column idempotently."""
    statement = text(
        """
        ALTER TABLE payments
        ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Final'
        """
    )
    with engine.begin() as connection:
        connection.execute(statement)


if __name__ == "__main__":
    add_payment_status_column()
    print("payments.status column is ready.")


## File: scripts\append_new_mandates.py
------------------------------
import os
import sys
from pathlib import Path

import pandas as pd

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from models.employer import Employer
from models.deposits import AnnualMandate


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "New_Mandates.xlsx"

# Unit conversion: Excel values are in Billion Rials, convert to base Rials
BILLION = 1_000_000_000

# Target fiscal year for the new mandates
TARGET_FISCAL_YEAR = 1406


def normalize_code(value):
    """Normalize employer code by removing .0 suffix from numeric strings."""
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.endswith(".0"):
        return value[:-2]
    return value


def append_new_mandates(file_path: Path = EXCEL_FILE_PATH, fiscal_year: int = TARGET_FISCAL_YEAR):
    """Append new mandate records to the annual_mandates table without dropping existing data."""
    
    print(f"=== Append New Mandates for Fiscal Year {fiscal_year} ===")
    print(f"Reading Excel file: {file_path}")
    
    # Read the Excel file
    df = pd.read_excel(file_path, engine='openpyxl')
    print(f"Loaded {len(df)} rows from Excel")
    print(f"Columns: {list(df.columns)}")
    
    # Validate required columns
    required_cols = ['شماره طبقه بندی', 'اعتبار تکلیفی']
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Normalize and prepare data
    df['employer_code'] = df['شماره طبقه بندی'].apply(normalize_code)
    df['mandated_amount'] = pd.to_numeric(df['اعتبار تکلیفی'], errors='coerce').fillna(0)
    
    # CRITICAL: Convert from Billion Rials to base Rials
    df['mandated_amount'] = df['mandated_amount'] * BILLION
    
    print(f"Converted amounts to base Rials (×{BILLION:,})")
    
    # Start database transaction
    db = SessionLocal()
    try:
        # Get valid employer codes from database
        valid_codes = {emp.classification_code for emp in db.query(Employer.classification_code).all()}
        print(f"Found {len(valid_codes)} valid employer codes in database")
        
        # Get existing mandates for this fiscal year
        existing_mandates = {
            (m.employer_code, m.fiscal_year) 
            for m in db.query(AnnualMandate.employer_code, AnnualMandate.fiscal_year)
                      .filter(AnnualMandate.fiscal_year == fiscal_year)
                      .all()
        }
        print(f"Found {len(existing_mandates)} existing mandates for fiscal year {fiscal_year}")
        
        # Process each row
        added = 0
        updated = 0
        skipped_missing_employer = 0
        skipped_duplicate = 0
        
        for idx, row in df.iterrows():
            employer_code = row['employer_code']
            mandated_amount = float(row['mandated_amount'])
            
            # Validation 1: Check if employer exists
            if employer_code not in valid_codes:
                print(f"WARNING: Row {idx} - employer_code '{employer_code}' not found in database. Skipping.")
                skipped_missing_employer += 1
                continue
            
            # Validation 2: Check for existing mandate
            if (employer_code, fiscal_year) in existing_mandates:
                # Update existing record instead of creating duplicate
                existing_mandate = db.query(AnnualMandate).filter_by(
                    employer_code=employer_code,
                    fiscal_year=fiscal_year
                ).first()
                
                if existing_mandate:
                    old_amount = existing_mandate.mandated_amount
                    existing_mandate.mandated_amount = mandated_amount
                    updated += 1
                    print(f"Updated: {employer_code} - Year {fiscal_year}: {old_amount:,.2f} → {mandated_amount:,.2f} Rials")
                continue
            
            # Insert new mandate
            new_mandate = AnnualMandate(
                employer_code=employer_code,
                fiscal_year=fiscal_year,
                mandated_amount=mandated_amount
            )
            db.add(new_mandate)
            added += 1
        
        # Commit transaction
        db.commit()
        
        print("\n=== Import Summary ===")
        print(f"✓ Successfully added {added} new Annual_Mandate records")
        print(f"✓ Successfully updated {updated} existing Annual_Mandate records")
        print(f"⚠ Skipped {skipped_missing_employer} rows due to missing employer codes")
        print(f"ℹ Skipped {skipped_duplicate} rows due to existing mandates (already handled via update)")
        print(f"\nNote: All monetary values converted from Billion Rials to base Rials (×{BILLION:,})")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: Database transaction failed. Rolled back.")
        print(f"Error details: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    append_new_mandates()


## File: scripts\chart01_total_trend.py
------------------------------
# chart01_total_trend.py
from chart_config import (
    load_data, fp, fmt_num, fa_year_formatter, CHARTS_DIR,
    COLORS, plt
)
import matplotlib.ticker as mticker
import numpy as np

df = load_data()

# ── آماده‌سازی داده ──────────────────────────────────────────────────────────
yearly = (
    df.groupby("سال")["اعتبار"]
    .sum()
    .reset_index()
    .sort_values("سال")
)

years  = yearly["سال"].tolist()
values = yearly["اعتبار"].tolist()

# رشد سال به سال (YoY)
yoy = [None] + [
    (values[i] - values[i-1]) / values[i-1] * 100
    for i in range(1, len(values))
]

# ── محور X: ایندکس مصنوعی برای فاصله یکنواخت ────────────────────────────────
# به جای مقادیر واقعی سال، از ایندکس 0,1,2,... استفاده می‌کنیم
# تا فاصله بین همه سال‌ها یکسان باشد
x_pos = list(range(len(years)))

# برچسب‌های فارسی سال + نشانگر ۱۴۰۳
FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
def to_fa(n):
    return str(n).translate(FA_DIGITS)

x_labels = [to_fa(y) for y in years]

# جایگاه ۱۴۰۳ بین ۱۴۰۲ و ۱۴۰۴
idx_1402 = years.index(1402)
x_1403 = (x_pos[idx_1402] + x_pos[idx_1402 + 1]) / 2  # دقیقاً وسط

# ── رسم نمودار ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6))

# خط اصلی
ax.plot(x_pos, values, color=COLORS["primary"], linewidth=2.5,
        marker="o", markersize=8, zorder=3)

# سایه زیر خط
ax.fill_between(x_pos, values, alpha=0.12, color=COLORS["primary"])

# برچسب مقدار و رشد روی هر نقطه
for xi, y, g in zip(x_pos, values, yoy):
    ax.annotate(
        fp(f"{fmt_num(y, 1)}"),
        xy=(xi, y),
        xytext=(0, 14),
        textcoords="offset points",
        ha="center", va="bottom",
        fontsize=9,
        color=COLORS["primary"],
    )
    if g is not None:
        sign  = "+" if g >= 0 else ""
        color = COLORS["accent"] if g >= 0 else COLORS["danger"]
        ax.annotate(
            fp(f"{sign}{fmt_num(g, 1)}٪"),
            xy=(xi, y),
            xytext=(0, -18),
            textcoords="offset points",
            ha="center", va="top",
            fontsize=8,
            color=color,
        )

# ── محورها ───────────────────────────────────────────────────────────────────
ax.set_xticks(x_pos)
ax.set_xticklabels(x_labels, fontsize=10)

ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda v, _: fp(fmt_num(v, 0)))
)
ax.set_ylabel(fp("اعتبار تکلیفی (میلیارد ریال)"), labelpad=10)

# ── خط نقطه‌چین ۱۴۰۳ ─────────────────────────────────────────────────────────
ax.axvline(x=x_1403, color=COLORS["neutral"], linewidth=1,
           linestyle="--", alpha=0.6, zorder=1)

# برچسب ۱۴۰۳ — بعد از رسم همه چیز، ylim را می‌گیریم
ax.figure.canvas.draw()  # محدوده Y را نهایی می‌کند
ymin, ymax = ax.get_ylim()
ax.text(
    x_1403 + 0.05, ymin + (ymax - ymin) * 0.03,
    fp("۱۴۰۳\n(اطلاعات\nموجود نیست)"),
    ha="left", va="bottom", fontsize=8,
    color=COLORS["neutral"],
    linespacing=1.5,
)

# ── عنوان و گرید ─────────────────────────────────────────────────────────────
ax.set_title(fp("روند کل اعتبارات تکلیفی پیوست ۳ قانون بودجه (۱۳۹۸–۱۴۰۵)"),
             pad=16, fontsize=14)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.grid(axis="x", linestyle=":", alpha=0.2)
ax.set_axisbelow(True)

# کمی فضای اضافه در بالا برای برچسب‌ها
ax.margins(x=0.06, y=0.15)  # به جای ax.margins(x=0.06)

fig.tight_layout()

# ── ذخیره ────────────────────────────────────────────────────────────────────
out = CHARTS_DIR / "chart01_total_trend.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"ذخیره شد: {out}")


## File: scripts\check_excel.py
------------------------------
import pandas as pd
import sys

df = pd.read_excel('data/University.xlsx')

# Write to file to avoid console encoding issues
output_path = 'data/excel_info.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(f"Total rows: {len(df)}\n")
    f.write(f"Total columns: {len(df.columns)}\n\n")
    f.write("Column names:\n")
    for i, col in enumerate(df.columns):
        f.write(f"  {i}: {col}\n")
    
    f.write("\n\nFirst 5 rows sample:\n")
    f.write(df.head(5).to_string())
    
    f.write("\n\nData types:\n")
    f.write(str(df.dtypes))

print(f"Information written to {output_path}")


## File: scripts\create_transfer_table.py
------------------------------
"""
Credit Transfer Table Initialization Script
Safely creates the credit_transfers table without dropping existing tables.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import Base, engine
from models.transfer import CreditTransfer


def main():
    print("=" * 60)
    print("Credit Transfer Table Initialization")
    print("=" * 60)
    
    print("\nCreating credit_transfers table...")
    
    try:
        # Create only the CreditTransfer table, leaving other tables intact
        Base.metadata.create_all(bind=engine, tables=[CreditTransfer.__table__])
        
        print("✓ Successfully created credit_transfers table")
        print("\nTable structure:")
        print("  - id (Integer, Primary Key)")
        print("  - source_employer_code (String, FK -> employers)")
        print("  - destination_employer_code (String, FK -> employers, default='128342')")
        print("  - broker_name (String, nullable)")
        print("  - fiscal_year (Integer, indexed)")
        print("  - amount (Numeric(22,0))")
        print("  - contract_tracking_code (String, FK -> contracts)")
        print("  - documentation (Text, nullable)")
        print("  - created_at, updated_at, is_deleted (from SoftDeleteMixin)")
        
        print("\n" + "=" * 60)
        print("✓ Table initialization completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())


## File: scripts\example_1.py
------------------------------
import sys
import os
import pandas as pd

# این دو خط، مسیر اصلی پروژه را به پایتون می‌شناسانند تا پوشه core را پیدا کند
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# حالا پایتون می‌تواند core.database را پیدا کند
from core.database import engine

def run_pandas_example():
    print("Connecting to database and fetching employers data...")
    
    # خواندن کل جدول مشمولین از دیتابیس
    df_employers = pd.read_sql_table('employers', con=engine)
    
    print(f"\nTotal employers loaded: {len(df_employers)}")
    
    # نمایش ۵ رکورد اول
    print("\nFirst 5 records:")
    print(df_employers.head())
    
    # یک مثال تحلیلی: تعداد مشمولین به تفکیک استان
    print("\nEmployers count by province:")
    province_counts = df_employers['province'].value_counts()
    print(province_counts)

if __name__ == "__main__":
    run_pandas_example()

## File: scripts\fix_university_names.py
------------------------------
"""One-off migration: standardize known university name variants.

The SATE Excel exports (e.g. ``data/Researchers_Add_In.xlsx``) reference
universities by their full official name, such as "دانشگاه علامه طباطبایی"
or "دانشگاه صنعتی شریف". Some rows already present in the ``universities``
table were loaded without the "دانشگاه " prefix, or with an alternate
Arabic/Persian spelling of the final "ی"/"ئ" character, so name-based
lookups (see ``scripts/import_researchers_upsert.py``) fail to match them.

This script renames each known variant to its canonical exact name using a
substring (``ILIKE``) search, so both the missing-prefix and the ی/ئ
spelling variant are caught by the same pattern.

Safety note: a substring match can be ambiguous. For example
``%صنعتی شریف%`` matches both the target record ("صنعتی شریف") and an
unrelated "پارک علم و فناوری دانشگاه صنعتی شریف" (a science & technology
park, not the university itself). To resolve this without guessing, each
rule first tries an *exact* (case-insensitive) name match against its
pattern; an exact hit is always the most specific possible match, so it is
used immediately without considering other substring matches. Only when no
exact match exists does the rule fall back to a substring (``ILIKE``)
search — and if that broader search still matches more than one active
row, the rule is reported and left untouched rather than risk renaming the
wrong organization.

Usage
-----
    python scripts/fix_university_names.py
"""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from models.university import University  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("fix_university_names")

# Name substring (matched with ILIKE, case-insensitive) -> canonical exact
# name. The substring stops just before the character that varies between
# known spellings (e.g. "طباطبا" is shared by both "طباطبایی" and
# "طباطبائی") so a single pattern catches the common variants.
NAME_FIX_MAPPING: dict[str, str] = {
    "علامه طباطبا": "دانشگاه علامه طباطبایی",
    "صنعتی شریف": "دانشگاه صنعتی شریف",
}


def find_exact_matching_universities(
    session: Session,
    name_pattern: str,
) -> list[University]:
    """Find active universities whose name exactly equals the pattern.

    An exact (case-insensitive) match is the most specific possible result,
    so callers should prefer it over a broader substring search.

    Args:
        session: Active SQLAlchemy session.
        name_pattern: The mapping rule's pattern, compared for equality.

    Returns:
        All active (``is_deleted == False``) universities whose name
        exactly equals ``name_pattern`` (case-insensitive).
    """
    return (
        session.query(University)
        .filter(
            University.is_deleted == False,  # noqa: E712
            University.name.ilike(name_pattern),
        )
        .all()
    )


def find_substring_matching_universities(
    session: Session,
    name_substring: str,
) -> list[University]:
    """Find active universities whose name contains the given substring.

    Args:
        session: Active SQLAlchemy session.
        name_substring: Substring to search for within ``University.name``.

    Returns:
        All active (``is_deleted == False``) universities whose name
        contains ``name_substring``.
    """
    return (
        session.query(University)
        .filter(
            University.is_deleted == False,  # noqa: E712
            University.name.ilike(f"%{name_substring}%"),
        )
        .all()
    )


def apply_name_fix(
    session: Session,
    name_substring: str,
    canonical_name: str,
) -> str:
    """Resolve one substring-to-canonical-name mapping rule.

    Lookup order, each unambiguous by construction, tried until one
    succeeds: (1) a row whose name already exactly equals
    ``canonical_name`` — the rule was already applied on a prior run;
    (2) a row whose name exactly equals ``name_substring`` — the
    not-yet-fixed variant; (3) only if neither exact lookup finds
    anything, a broader substring search, which is rejected if it turns
    out to match more than one active row.

    Args:
        session: Active SQLAlchemy session.
        name_substring: Substring (or exact name) identifying the
            university to rename.
        canonical_name: The exact standardized name to apply.

    Returns:
        One of ``"updated"``, ``"already_correct"``, ``"no_match"``, or
        ``"ambiguous"``, describing the outcome for this rule.
    """
    already_fixed = find_exact_matching_universities(session, canonical_name)
    if already_fixed:
        university = already_fixed[0]
        logger.info(
            "University '%s' (national_id=%s) already has the canonical "
            "name; no change needed.",
            canonical_name,
            university.national_id,
        )
        return "already_correct"

    matches = find_exact_matching_universities(session, name_substring)
    if not matches:
        matches = find_substring_matching_universities(session, name_substring)

    if not matches:
        logger.warning(
            "No active university matched pattern '%s'; skipped.",
            name_substring,
        )
        return "no_match"

    if len(matches) > 1:
        candidate_summary = ", ".join(
            f"{university.national_id}: '{university.name}'"
            for university in matches
        )
        logger.warning(
            "Pattern '%s' matched %d active universities (ambiguous, "
            "skipped): %s",
            name_substring,
            len(matches),
            candidate_summary,
        )
        return "ambiguous"

    university = matches[0]
    logger.info(
        "Renaming university national_id=%s: '%s' -> '%s'",
        university.national_id,
        university.name,
        canonical_name,
    )
    university.name = canonical_name
    return "updated"


def run_name_fix() -> None:
    """Apply every rule in ``NAME_FIX_MAPPING`` and print a final summary."""
    session = SessionLocal()
    outcome_counts = {
        "updated": 0,
        "already_correct": 0,
        "no_match": 0,
        "ambiguous": 0,
    }

    try:
        for name_substring, canonical_name in NAME_FIX_MAPPING.items():
            outcome = apply_name_fix(session, name_substring, canonical_name)
            outcome_counts[outcome] += 1
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Name fix failed, transaction rolled back: %s", exc)
        return
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("UNIVERSITY NAME FIX SUMMARY")
    print("=" * 60)
    print(f"Rules processed:            {len(NAME_FIX_MAPPING)}")
    print(f"Rows updated:               {outcome_counts['updated']}")
    print(f"Rows already correct:       {outcome_counts['already_correct']}")
    print(f"Rules with no match:        {outcome_counts['no_match']}")
    print(f"Rules skipped (ambiguous):  {outcome_counts['ambiguous']}")
    print("=" * 60)


if __name__ == "__main__":
    run_name_fix()


## File: scripts\generate_contract_status_report.py
------------------------------
"""Generate an Excel breakdown of dynamically calculated contract statuses."""

import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from services.financial_engine import get_contracts_with_dynamic_status


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "results" / "contract_status_breakdown.xlsx"
STATUS_ORDER = ["Completed", "Stagnant", "Active"]
STATUS_TRANSLATIONS = {
    "Completed": "خاتمه‌یافته",
    "Stagnant": "راکد",
    "Active": "فعال",
}
DETAIL_COLUMN_TRANSLATIONS = {
    "tracking_code": "کد رهگیری",
    "employer_code": "کد دستگاه",
    "university_id": "شناسه دانشگاه",
    "researcher_id": "کد ملی پژوهشگر",
    "proposal_id": "شناسه پیشنهاد",
    "contract_number": "شماره قرارداد",
    "contract_date": "تاریخ قرارداد",
    "contract_creation_year": "سال انعقاد (شمسی)",
    "total_amount": "مبلغ کل قرارداد (ریال)",
    "total_paid": "مجموع پرداختی (ریال)",
    "last_payment_funding_year": "سال تأمین اعتبار آخرین پرداخت",
    "activity_year": "سال آخرین فعالیت",
    "dynamic_status": "وضعیت قرارداد",
    "title": "عنوان قرارداد",
}
SUMMARY_COLUMN_TRANSLATIONS = {
    "contract_creation_year": "سال انعقاد (شمسی)",
    "Completed": "خاتمه‌یافته",
    "Stagnant": "راکد",
    "Active": "فعال",
    "Total": "مجموع",
}


def _results_to_dataframe(rows) -> pd.DataFrame:
    """Convert SQLAlchemy result rows into report-friendly contract records."""
    records = []
    for row in rows:
        contract = row.Contract
        records.append(
            {
                "tracking_code": contract.tracking_code,
                "employer_code": contract.employer_code,
                "university_id": contract.university_id,
                "researcher_id": contract.researcher_id,
                "proposal_id": contract.proposal_id,
                "contract_number": contract.contract_number,
                "contract_date": contract.contract_date,
                "contract_creation_year": int(row.contract_creation_year) if row.contract_creation_year is not None else None,
                "total_amount": contract.total_amount,
                "total_paid": row.total_paid,
                "last_payment_funding_year": row.last_payment_funding_year,
                "activity_year": int(row.activity_year) if row.activity_year is not None else None,
                "dynamic_status": row.dynamic_status,
                "title": contract.title,
            }
        )
    return pd.DataFrame(records)


def _build_summary(details: pd.DataFrame) -> pd.DataFrame:
    """Aggregate contract counts by Jalali creation year and dynamic status."""
    if details.empty:
        return pd.DataFrame(columns=["contract_creation_year", *STATUS_ORDER, "Total"])

    summary = pd.pivot_table(
        details,
        index="contract_creation_year",
        columns="dynamic_status",
        values="tracking_code",
        aggfunc="count",
        fill_value=0,
    )
    summary = summary.reindex(columns=STATUS_ORDER, fill_value=0)
    summary["Total"] = summary.sum(axis=1)
    return summary.reset_index().sort_values("contract_creation_year", na_position="last")


def main() -> None:
    """Generate detailed and aggregated contract status Excel worksheets."""
    db = SessionLocal()
    try:
        rows = get_contracts_with_dynamic_status(db, threshold_year=1402)
        details = _results_to_dataframe(rows)
        summary = _build_summary(details)

        if "dynamic_status" in details.columns:
            details["dynamic_status"] = details["dynamic_status"].replace(
                STATUS_TRANSLATIONS
            )
        details = details.rename(columns=DETAIL_COLUMN_TRANSLATIONS)
        summary = summary.rename(columns=SUMMARY_COLUMN_TRANSLATIONS)

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
            summary.to_excel(writer, sheet_name="Summary Dashboard", index=False)
            details.to_excel(writer, sheet_name="Detailed Data", index=False)

        print(f"Generated {OUTPUT_PATH}")
        print(f"Detailed contracts: {len(details)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()


## File: scripts\generate_financial_report.py
------------------------------
"""
Financial Report Generator
Exports employer balances using the centralized macro engine in financial_engine.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from services.financial_engine import get_all_employers_financials

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "results" / "financial_report_summary.xlsx"

PERSIAN_COLUMNS = [
    "کد مشمول",
    "نام مشمول",
    "سال مالی",
    "اعتبار تکلیفی (ریال)",
    "مجموع واریزی (ریال)",
    "هزینه کرد (ریال)",
    "انتقال ورودی (ریال)",
    "انتقال خروجی (ریال)",
    "مانده واقعی (ریال)",
]

COLUMN_MAPPING = {
    "employer_code": PERSIAN_COLUMNS[0],
    "employer_name": PERSIAN_COLUMNS[1],
    "year": PERSIAN_COLUMNS[2],
    "mandated_amount": PERSIAN_COLUMNS[3],
    "deposit_amount": PERSIAN_COLUMNS[4],
    "payment_amount": PERSIAN_COLUMNS[5],
    "transfer_in": PERSIAN_COLUMNS[6],
    "transfer_out": PERSIAN_COLUMNS[7],
    "balance": PERSIAN_COLUMNS[8],
}


def main():
    print("=" * 60)
    print("Financial Report Generator - Employer Balance Analysis")
    print("=" * 60)

    db = SessionLocal()
    try:
        print("\n[1/3] Calculating employer financials via macro engine...")
        df = get_all_employers_financials(db)

        if df.empty:
            print("   No financial data found.")
            return

        print(f"   Loaded {df['employer_code'].nunique()} employers")
        print(f"   Generated {len(df)} employer-year records")

        print("\n[2/3] Formatting report columns...")
        df_report = df.rename(columns=COLUMN_MAPPING)
        df_report = df_report.sort_values([PERSIAN_COLUMNS[0], PERSIAN_COLUMNS[2]])

        print("\n[3/3] Exporting to Excel...")
        OUTPUT_PATH.parent.mkdir(exist_ok=True)
        df_report.to_excel(OUTPUT_PATH, index=False, engine="openpyxl")
        print(f"   Exported to: {OUTPUT_PATH}")

        print("\n" + "=" * 60)
        print("REPORT SUMMARY")
        print("=" * 60)
        print(f"Total employers:        {df_report[PERSIAN_COLUMNS[0]].nunique()}")
        print(f"Total fiscal years:     {df_report[PERSIAN_COLUMNS[2]].nunique()}")
        print(
            f"Total mandated amount:  "
            f"{df_report[PERSIAN_COLUMNS[3]].sum():,.0f} Rials"
        )
        print(
            f"Total deposited:        "
            f"{df_report[PERSIAN_COLUMNS[4]].sum():,.0f} Rials"
        )
        print(
            f"Total payments:         "
            f"{df_report[PERSIAN_COLUMNS[5]].sum():,.0f} Rials"
        )
        print(
            f"Total transfers in:     "
            f"{df_report[PERSIAN_COLUMNS[6]].sum():,.0f} Rials"
        )
        print(
            f"Total transfers out:    "
            f"{df_report[PERSIAN_COLUMNS[7]].sum():,.0f} Rials"
        )
        print(
            f"Total real balance:     "
            f"{df_report[PERSIAN_COLUMNS[8]].sum():,.0f} Rials"
        )
        print("=" * 60)
        print("\nFinancial report generation completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    main()


## File: scripts\import_contracts.py
------------------------------
import pandas as pd
import sys
from pathlib import Path
import io
from decimal import Decimal

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import engine, Base
from core.date_helper import parse_strict_jalali_date
from models.contract import Contract
from models.employer import Employer
from models.university import University
from models.researchers import Researcher


def parse_persian_date(date_str):
    """Parse a Jalali date strictly and return a Gregorian date."""
    if pd.isna(date_str) or not date_str:
        return None

    try:
        return parse_strict_jalali_date(str(date_str))
    except (TypeError, ValueError) as exc:
        print(f"  [WARNING] Invalid date format: {date_str} - {exc}")
        return None


def import_contracts():
    """Import contracts from Excel file"""
    
    # Drop contracts table with CASCADE to handle FK dependencies
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS contracts CASCADE"))
    print("[OK] Dropped contracts table with CASCADE")
    
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created/verified")
    
    # Read Excel file
    excel_path = "data/Contracts.xlsx"
    print(f"Reading Excel from: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
        print(f"[OK] Loaded {len(df)} rows from Excel")
    except FileNotFoundError:
        print(f"[ERROR] Excel file not found at {excel_path}")
        return
    except Exception as e:
        print(f"[ERROR] Error reading Excel: {e}")
        return
    
    print(f"Excel has {len(df.columns)} columns")
    
    # Column mapping (Persian headers to model fields)
    column_mapping = {
        'کد رهگیری': 'tracking_code',
        'شماره طبقه بندی': 'employer_code',
        'شناسه ملی موسسه': 'university_id',
        'کد ملی فناور': 'researcher_id',
        'شناسه پیشنهاده': 'proposal_id',
        'شماره قرارداد': 'contract_number',
        'تاریخ قرارداد': 'contract_date',
        'مبلغ قرارداد(ریال)': 'total_amount',
        'عنوان قرارداد': 'title',
        'مدت زمان اجرا (ماه)': 'duration_months',
        'وضعیت': 'status'
    }
    
    # Start database session
    session = Session(bind=engine)
    
    try:
        # Performance optimization: Query all valid FK values once (avoid N+1)
        print("Fetching valid foreign key references...")
        
        valid_employer_codes = set(
            code for (code,) in session.query(Employer.classification_code).filter(
                Employer.is_deleted == False
            ).all()
        )
        print(f"[OK] Found {len(valid_employer_codes)} valid employer codes")
        
        valid_university_ids = set(
            uid for (uid,) in session.query(University.national_id).filter(
                University.is_deleted == False
            ).all()
        )
        print(f"[OK] Found {len(valid_university_ids)} valid university IDs")
        
        valid_researcher_ids = set(
            rid for (rid,) in session.query(Researcher.national_code).filter(
                Researcher.is_deleted == False
            ).all()
        )
        print(f"[OK] Found {len(valid_researcher_ids)} valid researcher IDs")
        
        # Query existing tracking codes to avoid duplicates
        existing_tracking_codes = set(
            code for (code,) in session.query(Contract.tracking_code).filter(
                Contract.is_deleted == False
            ).all()
        )
        print(f"[OK] Found {len(existing_tracking_codes)} existing contracts in database")
        
        # Counters
        added_count = 0
        skipped_duplicate = 0
        skipped_fk_employer = 0
        skipped_fk_university = 0
        skipped_fk_researcher = 0
        skipped_invalid = 0
        error_count = 0
        
        print("\nProcessing records...")
        
        # Iterate through dataframe
        for index, row in df.iterrows():
            try:
                # Get tracking_code (primary key)
                tracking_code = row.get('کد رهگیری')
                
                # Convert pandas NaN to None and strip whitespaces
                tracking_code = None if pd.isna(tracking_code) else str(tracking_code).strip()
                
                # Skip if tracking_code is empty or already exists
                if not tracking_code:
                    skipped_invalid += 1
                    continue
                    
                if tracking_code in existing_tracking_codes:
                    skipped_duplicate += 1
                    continue
                
                # Get and validate FKs
                employer_code = row.get('شماره طبقه بندی')
                employer_code = None if pd.isna(employer_code) else str(employer_code).strip()
                
                university_id = row.get('شناسه ملی موسسه')
                university_id = None if pd.isna(university_id) else str(university_id).strip()
                
                researcher_id = row.get('کد ملی فناور')
                researcher_id = None if pd.isna(researcher_id) else str(researcher_id).strip()
                
                # Validate FK integrity - skip row if any FK is invalid
                if not employer_code or employer_code not in valid_employer_codes:
                    skipped_fk_employer += 1
                    if employer_code:
                        print(f"  [FK_SKIP] Row {index + 1}: Invalid employer_code '{employer_code}'")
                    continue
                
                if not university_id or university_id not in valid_university_ids:
                    skipped_fk_university += 1
                    if university_id:
                        print(f"  [FK_SKIP] Row {index + 1}: Invalid university_id '{university_id}'")
                    continue
                
                if not researcher_id or researcher_id not in valid_researcher_ids:
                    skipped_fk_researcher += 1
                    if researcher_id:
                        print(f"  [FK_SKIP] Row {index + 1}: Invalid researcher_id '{researcher_id}'")
                    continue
                
                # Prepare contract data
                contract_data = {
                    'tracking_code': tracking_code,
                    'employer_code': employer_code,
                    'university_id': university_id,
                    'researcher_id': researcher_id
                }
                
                # Map other fields
                for persian_col, field_name in column_mapping.items():
                    if field_name in ['tracking_code', 'employer_code', 'university_id', 'researcher_id']:
                        continue  # Already handled
                    
                    value = row.get(persian_col)
                    
                    # Handle date conversion
                    if field_name == 'contract_date':
                        contract_data[field_name] = parse_persian_date(value)
                    # Handle numeric fields
                    elif field_name == 'total_amount':
                        if pd.isna(value):
                            contract_data[field_name] = 0
                        else:
                            try:
                                contract_data[field_name] = Decimal(str(value))
                            except:
                                contract_data[field_name] = 0
                    elif field_name == 'duration_months':
                        if pd.isna(value):
                            contract_data[field_name] = None
                        else:
                            try:
                                contract_data[field_name] = int(value)
                            except:
                                contract_data[field_name] = None
                    # Handle strings
                    else:
                        if pd.isna(value):
                            contract_data[field_name] = None
                        elif isinstance(value, str):
                            contract_data[field_name] = value.strip()
                        else:
                            contract_data[field_name] = str(value)
                
                # Validate required fields
                if not contract_data.get('title'):
                    skipped_invalid += 1
                    continue
                
                # Set defaults for nullable fields
                if contract_data.get('status') is None:
                    contract_data['status'] = 'Active'
                
                # Create Contract instance
                contract = Contract(**contract_data)
                session.add(contract)
                
                # Add to existing set to prevent duplicates in same batch
                existing_tracking_codes.add(tracking_code)
                added_count += 1
                
                # Commit in batches of 100
                if added_count % 100 == 0:
                    session.commit()
                    print(f"  Progress: {added_count} contracts added")
                
            except Exception as e:
                error_count += 1
                print(f"  [ERROR] Row {index + 1}: {str(e)}")
                session.rollback()
                continue
        
        # Final commit
        session.commit()
        
        # Summary
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"[OK] Successfully imported: {added_count} contracts")
        print(f"[SKIP] Duplicates/empty tracking codes: {skipped_duplicate + skipped_invalid}")
        print(f"[FK_SKIP] Invalid employer_code: {skipped_fk_employer}")
        print(f"[FK_SKIP] Invalid university_id: {skipped_fk_university}")
        print(f"[FK_SKIP] Invalid researcher_id: {skipped_fk_researcher}")
        total_fk_skips = skipped_fk_employer + skipped_fk_university + skipped_fk_researcher
        print(f"[FK_SKIP] Total FK mismatches: {total_fk_skips}")
        print(f"[ERROR] Processing errors: {error_count}")
        print(f"Total rows processed: {len(df)}")
        print("="*60)
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Fatal error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    print("="*60)
    print("CONTRACT IMPORT SCRIPT")
    print("="*60)
    import_contracts()


## File: scripts\import_contracts_upsert.py
------------------------------
"""Idempotent upsert ETL for the ``contracts`` table.

Loads contract records from an Excel workbook and writes them to
PostgreSQL using a single native ``INSERT ... ON CONFLICT (tracking_code)
DO UPDATE`` statement (via ``sqlalchemy.dialects.postgresql.insert``). Like
``scripts/import_universities_upsert.py`` and
``scripts/import_researchers_upsert.py``, this script never drops the
table and never performs an application-level "SELECT then INSERT/UPDATE"
check for the conflict target — PostgreSQL resolves the insert-vs-update
race atomically.

Triple FK resolution: the source file has no ``employer_code``,
``university_id``, or ``researcher_id`` columns — only free-text names for
Employer (``متقاضی``), University (``دانشگاه``), and Researcher
(``فناور``). Three lookups are built once from the database before any row
is processed:

* ``employer_lookup``  : ``{name.strip(): (classification_code, employer_type)}``
* ``university_lookup``: ``{name.strip(): national_id}``
* ``researcher_lookup`` : ``{(full_name.strip(), university_id): national_code}``

The researcher lookup is keyed on ``(full_name, university_id)`` rather
than name alone, since two researchers can share a name across different
universities; resolving the researcher therefore requires the row's
university to have resolved first.

Business rule (see ``models/employer.py`` / ``api/v1/endpoints/contracts.py``):
contracts may only be registered under a ``Mother`` or ``Independent``
employer, never a ``Subsidiary``. This is why ``employer_lookup`` carries
the employer type alongside its code — a row whose employer resolves by
name but is a ``Subsidiary`` is skipped exactly like an unresolved
employer, since neither case yields a contractable employer.

Soft-delete interaction: if a ``tracking_code`` re-appears in the source
file after having been soft-deleted (``is_deleted = True``), the update
clause forces ``is_deleted = False``, restoring the record.

Usage
-----
    python scripts/import_contracts_upsert.py
"""

from __future__ import annotations

import io
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from core.date_helper import parse_strict_jalali_date  # noqa: E402
from models.contract import Contract  # noqa: E402
from models.employer import Employer  # noqa: E402
from models.researchers import Researcher  # noqa: E402
from models.university import University  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("import_contracts_upsert")

SOURCE_EXCEL_PATH = PROJECT_ROOT / "data" / "Contracts_Add_In.xlsx"

EMPLOYER_LOOKUP_COLUMN = "متقاضی"
UNIVERSITY_LOOKUP_COLUMN = "دانشگاه"
RESEARCHER_LOOKUP_COLUMN = "فناور"

# Per the system's immutable business rule: contracts may only be
# registered under a Mother or Independent employer, never a Subsidiary.
ALLOWED_CONTRACT_EMPLOYER_TYPES = {"Mother", "Independent"}

DEFAULT_STATUS = "Active"

# Columns refreshed on conflict. ``is_deleted`` is appended separately below
# so a soft-deleted row is always restored, regardless of the source value.
UPDATABLE_COLUMNS = (
    "employer_code",
    "university_id",
    "researcher_id",
    "proposal_id",
    "contract_number",
    "contract_date",
    "total_amount",
    "title",
    "duration_months",
    "status",
)


class RowSkipped(Exception):
    """Raised internally when a row cannot be converted to a valid record.

    Attributes
    ----------
    reason : str
        One of ``"missing_employer"``, ``"missing_university"``,
        ``"missing_researcher"``, ``"bad_date"``, or ``"invalid_data"``,
        used to route the row into the correct summary counter.
    """

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def load_source_dataframe(excel_path: Path) -> pd.DataFrame:
    """Read the source workbook into a DataFrame.

    Args:
        excel_path: Absolute path to the contract Excel workbook.

    Returns:
        The raw, unmodified worksheet contents.

    Raises:
        FileNotFoundError: If ``excel_path`` does not exist.
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Source Excel file not found: {excel_path}")

    dataframe = pd.read_excel(excel_path, engine="openpyxl")
    logger.info("Loaded %d rows from %s", len(dataframe), excel_path.name)
    return dataframe


def _clean_optional_text(value: Any) -> str | None:
    """Normalize an optional Excel cell to a stripped string or ``None``."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _strip_numeric_artifact(value: str) -> str:
    """Trim pandas' trailing ``.0`` float artifact from a numeric-looking ID."""
    if value.endswith(".0"):
        return value[:-2]
    return value


def _normalize_tracking_code(value: Any) -> str | None:
    """Normalize the primary-key column, stripping pandas' float artifacts."""
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    return _strip_numeric_artifact(cleaned)


def build_employer_lookup(session: Session) -> dict[str, tuple[str, str]]:
    """Build a ``{stripped employer name: (classification_code, employer_type)}`` map.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from whitespace-stripped, active employer name to its
        ``(classification_code, employer_type)``. When two active
        employers share a stripped name, the last one read wins and a
        warning is logged.
    """
    rows = (
        session.query(
            Employer.name, Employer.classification_code, Employer.employer_type
        )
        .filter(Employer.is_deleted == False)  # noqa: E712
        .all()
    )

    lookup: dict[str, tuple[str, str]] = {}
    for name, classification_code, employer_type in rows:
        if name is None:
            continue
        key = name.strip()
        if key in lookup and lookup[key][0] != classification_code:
            logger.warning(
                "Duplicate employer name '%s' maps to multiple "
                "classification_code values; using the last one seen.",
                key,
            )
        lookup[key] = (classification_code, employer_type)

    logger.info("Built employer lookup with %d entries.", len(lookup))
    return lookup


def build_university_lookup(session: Session) -> dict[str, str]:
    """Build a ``{stripped university name: national_id}`` lookup map.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from whitespace-stripped, active university name to its
        ``national_id``.
    """
    rows = (
        session.query(University.name, University.national_id)
        .filter(University.is_deleted == False)  # noqa: E712
        .all()
    )

    lookup: dict[str, str] = {}
    for name, national_id in rows:
        if name is None:
            continue
        key = name.strip()
        if key in lookup and lookup[key] != national_id:
            logger.warning(
                "Duplicate university name '%s' maps to multiple "
                "national_id values; using the last one seen.",
                key,
            )
        lookup[key] = national_id

    logger.info("Built university lookup with %d entries.", len(lookup))
    return lookup


def build_researcher_lookup(session: Session) -> dict[tuple[str, str], str]:
    """Build a ``{(full_name, university_id): national_code}`` lookup map.

    The composite key prevents cross-matching two different researchers
    who happen to share a full name at different universities.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from ``(stripped full_name, university_id)`` to the
        active researcher's ``national_code``.
    """
    rows = (
        session.query(
            Researcher.full_name, Researcher.university_id, Researcher.national_code
        )
        .filter(Researcher.is_deleted == False)  # noqa: E712
        .all()
    )

    lookup: dict[tuple[str, str], str] = {}
    for full_name, university_id, national_code in rows:
        if full_name is None:
            continue
        key = (full_name.strip(), university_id)
        lookup[key] = national_code

    logger.info("Built researcher lookup with %d entries.", len(lookup))
    return lookup


def resolve_employer_code(
    row: pd.Series,
    employer_lookup: dict[str, tuple[str, str]],
) -> str:
    """Resolve a row's free-text employer name to a ``classification_code``.

    Args:
        row: A single row from the source DataFrame.
        employer_lookup: Mapping built by :func:`build_employer_lookup`.

    Returns:
        The matching employer's ``classification_code``.

    Raises:
        RowSkipped: If the employer name is blank, does not match any
            active employer, or resolves to a ``Subsidiary`` employer
            (ineligible to hold a contract).
    """
    raw_name = _clean_optional_text(row.get(EMPLOYER_LOOKUP_COLUMN))
    if raw_name is None:
        raise RowSkipped(
            "missing_employer", f"Blank '{EMPLOYER_LOOKUP_COLUMN}' value."
        )

    resolved = employer_lookup.get(raw_name.strip())
    if resolved is None:
        raise RowSkipped(
            "missing_employer",
            f"Employer '{raw_name}' not found among active employers.",
        )

    classification_code, employer_type = resolved
    if employer_type not in ALLOWED_CONTRACT_EMPLOYER_TYPES:
        raise RowSkipped(
            "missing_employer",
            f"Employer '{raw_name}' is a '{employer_type}' employer; only "
            f"{sorted(ALLOWED_CONTRACT_EMPLOYER_TYPES)} may hold contracts.",
        )
    return classification_code


def resolve_university_id(
    row: pd.Series,
    university_lookup: dict[str, str],
) -> str:
    """Resolve a row's free-text institution name to a ``university_id``.

    Args:
        row: A single row from the source DataFrame.
        university_lookup: Mapping built by :func:`build_university_lookup`.

    Returns:
        The matching university's ``national_id``.

    Raises:
        RowSkipped: If the institution name is blank or does not match any
            active university.
    """
    raw_name = _clean_optional_text(row.get(UNIVERSITY_LOOKUP_COLUMN))
    if raw_name is None:
        raise RowSkipped(
            "missing_university", f"Blank '{UNIVERSITY_LOOKUP_COLUMN}' value."
        )

    university_id = university_lookup.get(raw_name.strip())
    if university_id is None:
        raise RowSkipped(
            "missing_university",
            f"Institution '{raw_name}' not found among active universities.",
        )
    return university_id


def resolve_researcher_id(
    row: pd.Series,
    university_id: str,
    researcher_lookup: dict[tuple[str, str], str],
) -> str:
    """Resolve a row's free-text researcher name to a ``national_code``.

    Args:
        row: A single row from the source DataFrame.
        university_id: The row's already-resolved ``university_id``, used
            as the second half of the composite lookup key.
        researcher_lookup: Mapping built by :func:`build_researcher_lookup`.

    Returns:
        The matching researcher's ``national_code``.

    Raises:
        RowSkipped: If the researcher name is blank or does not match any
            active researcher at the resolved university.
    """
    raw_name = _clean_optional_text(row.get(RESEARCHER_LOOKUP_COLUMN))
    if raw_name is None:
        raise RowSkipped(
            "missing_researcher", f"Blank '{RESEARCHER_LOOKUP_COLUMN}' value."
        )

    national_code = researcher_lookup.get((raw_name.strip(), university_id))
    if national_code is None:
        raise RowSkipped(
            "missing_researcher",
            f"Researcher '{raw_name}' not found at university_id "
            f"'{university_id}'.",
        )
    return national_code


def parse_contract_date(row: pd.Series) -> date | None:
    """Strictly parse the Jalali contract-date column.

    Args:
        row: A single row from the source DataFrame.

    Returns:
        The equivalent Gregorian date, or ``None`` if the source cell is
        blank (``contract_date`` is a nullable column).

    Raises:
        RowSkipped: If the cell holds a non-blank value that fails strict
            Jalali calendar validation.
    """
    raw_value = row.get("تاریخ قرارداد")
    if pd.isna(raw_value):
        return None

    try:
        return parse_strict_jalali_date(str(raw_value))
    except (TypeError, ValueError) as exc:
        raise RowSkipped(
            "bad_date", f"Invalid Jalali contract date '{raw_value}': {exc}"
        ) from exc


def _clean_total_amount(row: pd.Series) -> int:
    """Parse the contract amount into a whole-Rial integer.

    Raises:
        RowSkipped: If the amount is blank or not a valid number.
    """
    raw_value = row.get("مبلغ قرارداد(ریال)")
    if pd.isna(raw_value):
        raise RowSkipped("invalid_data", "Missing total_amount.")
    try:
        return int(float(raw_value))
    except (TypeError, ValueError) as exc:
        raise RowSkipped(
            "invalid_data", f"Non-numeric total_amount '{raw_value}': {exc}"
        ) from exc


def _clean_duration_months(row: pd.Series) -> int | None:
    """Parse the optional contract duration into an integer month count."""
    raw_value = row.get("مدت زمان اجرا (ماه)")
    if pd.isna(raw_value):
        return None
    try:
        return int(float(raw_value))
    except (TypeError, ValueError):
        return None


def row_to_contract_record(
    row: pd.Series,
    employer_lookup: dict[str, tuple[str, str]],
    university_lookup: dict[str, str],
    researcher_lookup: dict[tuple[str, str], str],
) -> dict[str, Any]:
    """Convert one Excel row into a sanitized ``contracts`` row dict.

    Args:
        row: A single row from the source DataFrame.
        employer_lookup: Mapping built by :func:`build_employer_lookup`.
        university_lookup: Mapping built by :func:`build_university_lookup`.
        researcher_lookup: Mapping built by :func:`build_researcher_lookup`.

    Returns:
        A dict ready for the upsert statement.

    Raises:
        RowSkipped: If the row is missing a required field, its employer,
            university, or researcher cannot be resolved, or its contract
            date fails strict Jalali validation.
    """
    tracking_code = _normalize_tracking_code(row.get("کد رهگیری"))
    if tracking_code is None:
        raise RowSkipped("invalid_data", "Missing tracking_code.")

    title = _clean_optional_text(row.get("عنوان قرارداد"))
    if title is None:
        raise RowSkipped(
            "invalid_data", f"Missing title for tracking_code '{tracking_code}'."
        )

    # Resolution order matches the spec: employer, then university, then
    # researcher (which depends on the resolved university_id).
    employer_code = resolve_employer_code(row, employer_lookup)
    university_id = resolve_university_id(row, university_lookup)
    researcher_id = resolve_researcher_id(row, university_id, researcher_lookup)

    contract_date = parse_contract_date(row)
    total_amount = _clean_total_amount(row)
    duration_months = _clean_duration_months(row)

    proposal_id = _clean_optional_text(row.get("شناسه پیشنهاده"))
    if proposal_id is not None:
        proposal_id = _strip_numeric_artifact(proposal_id)

    record: dict[str, Any] = {
        "tracking_code": tracking_code,
        "employer_code": employer_code,
        "university_id": university_id,
        "researcher_id": researcher_id,
        "proposal_id": proposal_id,
        "contract_number": _clean_optional_text(row.get("شماره قرارداد")),
        "contract_date": contract_date,
        "total_amount": total_amount,
        "title": title,
        "duration_months": duration_months,
        "status": _clean_optional_text(row.get("وضعیت")) or DEFAULT_STATUS,
        "is_deleted": False,
    }
    return record


def transform_dataframe(
    dataframe: pd.DataFrame,
    employer_lookup: dict[str, tuple[str, str]],
    university_lookup: dict[str, str],
    researcher_lookup: dict[tuple[str, str], str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Convert every Excel row to sanitized upsert records.

    Duplicate ``tracking_code`` values within the source file are
    collapsed to the last occurrence, since PostgreSQL rejects an
    ``ON CONFLICT`` batch that targets the same conflict key twice.

    Args:
        dataframe: The raw source worksheet.
        employer_lookup: Mapping built by :func:`build_employer_lookup`.
        university_lookup: Mapping built by :func:`build_university_lookup`.
        researcher_lookup: Mapping built by :func:`build_researcher_lookup`.

    Returns:
        A tuple of (deduplicated records ready for upsert, skip counters
        keyed by reason).
    """
    records_by_tracking_code: dict[str, dict[str, Any]] = {}
    skip_counts = {
        "missing_employer": 0,
        "missing_university": 0,
        "missing_researcher": 0,
        "bad_date": 0,
        "invalid_data": 0,
    }

    for index, row in dataframe.iterrows():
        excel_row_number = index + 2  # 1-indexed plus header row offset.
        try:
            record = row_to_contract_record(
                row, employer_lookup, university_lookup, researcher_lookup
            )
        except RowSkipped as exc:
            skip_counts[exc.reason] += 1
            logger.warning("Row %d skipped: %s", excel_row_number, exc)
            continue

        records_by_tracking_code[record["tracking_code"]] = record

    return list(records_by_tracking_code.values()), skip_counts


def build_upsert_statement(records: list[dict[str, Any]]):
    """Build the native PostgreSQL ``INSERT ... ON CONFLICT DO UPDATE`` statement.

    All rows are batched into a single statement so the entire import
    commits atomically and PostgreSQL — not the application — resolves the
    insert-vs-update race for each ``tracking_code``.

    Args:
        records: Sanitized rows produced by :func:`transform_dataframe`.

    Returns:
        An executable SQLAlchemy ``Insert`` construct with the upsert
        clause attached.
    """
    insert_statement = pg_insert(Contract).values(records)

    update_columns = {
        column: getattr(insert_statement.excluded, column)
        for column in UPDATABLE_COLUMNS
    }
    # Always restore a previously soft-deleted record on re-import.
    update_columns["is_deleted"] = False

    return insert_statement.on_conflict_do_update(
        index_elements=[Contract.tracking_code],
        set_=update_columns,
    )


def run_upsert_import() -> None:
    """Execute the end-to-end upsert import and print a final summary."""
    try:
        dataframe = load_source_dataframe(SOURCE_EXCEL_PATH)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return

    session = SessionLocal()
    try:
        employer_lookup = build_employer_lookup(session)
        university_lookup = build_university_lookup(session)
        researcher_lookup = build_researcher_lookup(session)
    except SQLAlchemyError as exc:
        logger.error("Failed to build lookup tables: %s", exc)
        session.close()
        return

    records, skip_counts = transform_dataframe(
        dataframe, employer_lookup, university_lookup, researcher_lookup
    )

    if not records:
        logger.warning("No valid rows to upsert; nothing was written.")
        session.close()
        return

    statement = build_upsert_statement(records)

    try:
        result = session.execute(statement)
        session.commit()
        processed_count = result.rowcount
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Upsert failed, transaction rolled back: %s", exc)
        return
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("CONTRACT UPSERT SUMMARY")
    print("=" * 60)
    print(f"Source rows read:                 {len(dataframe)}")
    print(f"Skipped (missing employer):        {skip_counts['missing_employer']}")
    print(f"Skipped (missing university):      {skip_counts['missing_university']}")
    print(f"Skipped (missing researcher):      {skip_counts['missing_researcher']}")
    print(f"Skipped (bad contract date):       {skip_counts['bad_date']}")
    print(f"Skipped (other invalid data):      {skip_counts['invalid_data']}")
    print(f"Rows processed (upsert):           {processed_count}")
    print("=" * 60)


if __name__ == "__main__":
    run_upsert_import()


## File: scripts\import_credit_transfers.py
------------------------------
"""
ETL Script: Import Credit Transfers from Excel
Imports credit transfer data with validation and business logic checks
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from core.database import SessionLocal, engine
from models.transfer import CreditTransfer
from models.contract import Contract
from models.employer import Employer
from services.financial_engine import calculate_real_balance

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "CreditTransfer.xlsx"


def clean_amount(value):
    """Remove thousand separators (commas and dots) and convert to numeric Rials."""
    if pd.isna(value):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    cleaned = str(value).replace(',', '').replace('.', '').strip()
    if not cleaned:
        return 0
    try:
        return int(float(cleaned))
    except ValueError:
        return 0


def import_credit_transfers():
    """Main ETL function to import credit transfers"""
    
    print("=" * 70)
    print("Credit Transfer Import Process Started")
    print("=" * 70)
    
    # Statistics counters
    total_rows = 0
    inserted_rows = 0
    skipped_fk_errors = 0
    skipped_insufficient_funds = 0
    
    # Step 1: Drop and recreate table
    print("\n[1/6] Dropping and recreating credit_transfers table...")
    CreditTransfer.__table__.drop(engine, checkfirst=True)
    CreditTransfer.__table__.create(engine, checkfirst=True)
    print("✓ Table recreated successfully")
    
    # Step 2: Read Excel file
    print("\n[2/6] Reading Excel file...")
    if not EXCEL_FILE_PATH.is_file():
        print(f"✗ Excel file not found: {EXCEL_FILE_PATH}")
        return
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        total_rows = len(df)
        print(f"✓ Loaded {total_rows} rows from {EXCEL_FILE_PATH.name}")
    except Exception as e:
        print(f"✗ Error reading Excel file: {e}")
        return
    
    # Step 3: Load validation sets
    print("\n[3/6] Loading validation data...")
    db = SessionLocal()
    try:
        # Load all valid employer codes
        valid_employers = set(
            db.query(Employer.classification_code)
            .filter(Employer.is_deleted == False)
            .all()
        )
        valid_employer_codes = {code[0] for code in valid_employers}
        
        # Load all valid contract tracking codes
        valid_contracts = set(
            db.query(Contract.tracking_code)
            .filter(Contract.is_deleted == False)
            .all()
        )
        valid_contract_codes = {code[0] for code in valid_contracts}
        
        print(f"✓ Loaded {len(valid_employer_codes)} valid employer codes")
        print(f"✓ Loaded {len(valid_contract_codes)} valid contract codes")
        
    except Exception as e:
        print(f"✗ Error loading validation data: {e}")
        db.close()
        return
    
    # Step 4: Column mapping
    print("\n[4/6] Mapping columns...")
    column_mapping = {
        'شماره طبقه بندی شرکت مبدأ': 'source_employer_code',
        'شماره طبقه بندی شرکت مقصد': 'destination_employer_code',
        'کارگزار قرارداد': 'broker_name',
        'انتقال از محل سال مالی': 'fiscal_year',
        'مبلغ انتقال (ریال)': 'amount',
        'کد رهگیری قرارداد': 'contract_tracking_code'
    }

    missing_columns = [col for col in column_mapping if col not in df.columns]
    if missing_columns:
        print("✗ Missing expected columns in Excel file:")
        for col in missing_columns:
            print(f"  - {col}")
        print(f"  Found columns: {list(df.columns)}")
        db.close()
        return

    df = df.rename(columns=column_mapping)
    print("✓ Columns mapped successfully")
    
    # Step 5: Process and validate rows
    print("\n[5/6] Processing rows with validation...")
    print("-" * 70)
    
    for idx, row in df.iterrows():
        row_num = idx + 1
        
        # Extract and clean data
        source_code = str(row.get('source_employer_code', '')).strip()
        dest_code = str(row.get('destination_employer_code', '')).strip()
        broker = str(row.get('broker_name', '')).strip() if pd.notna(row.get('broker_name')) else None
        
        try:
            fiscal_year = int(row.get('fiscal_year', 0))
        except (ValueError, TypeError):
            print(f"⚠ Row {row_num}: Invalid fiscal year, skipping")
            skipped_fk_errors += 1
            continue
        
        amount = clean_amount(row.get('amount'))
        if amount <= 0:
            print(f"⚠ Row {row_num}: Invalid or zero amount ({row.get('amount')!r}), skipping")
            skipped_fk_errors += 1
            continue

        contract_code = str(row.get('contract_tracking_code', '')).strip()
        
        # Validation 1: Check foreign key constraints
        if source_code not in valid_employer_codes:
            print(f"⚠ Row {row_num}: Invalid source employer '{source_code}', skipping")
            skipped_fk_errors += 1
            continue
        
        if dest_code not in valid_employer_codes:
            print(f"⚠ Row {row_num}: Invalid destination employer '{dest_code}', skipping")
            skipped_fk_errors += 1
            continue
        
        if contract_code not in valid_contract_codes:
            print(f"⚠ Row {row_num}: Invalid contract '{contract_code}', skipping")
            skipped_fk_errors += 1
            continue
        
        # Validation 2: Check balance (Business Logic)
        try:
            current_balance = calculate_real_balance(db, source_code, fiscal_year)
            
            if current_balance < amount:
                print(f"⚠ Row {row_num}: INSUFFICIENT FUNDS for employer '{source_code}'")
                print(f"  Current balance: {current_balance:,.0f} Rials")
                print(f"  Transfer amount: {amount:,.0f} Rials")
                print(f"  Deficit: {(amount - current_balance):,.0f} Rials")
                skipped_insufficient_funds += 1
                continue
                
        except Exception as e:
            print(f"⚠ Row {row_num}: Error calculating balance: {e}, skipping")
            skipped_fk_errors += 1
            continue
        
        # Insert valid row
        try:
            credit_transfer = CreditTransfer(
                source_employer_code=source_code,
                destination_employer_code=dest_code,
                broker_name=broker,
                fiscal_year=fiscal_year,
                amount=amount,
                contract_tracking_code=contract_code
            )
            
            db.add(credit_transfer)
            inserted_rows += 1
            
            if inserted_rows % 10 == 0:
                print(f"✓ Processed {inserted_rows} valid transfers...")
                
        except Exception as e:
            print(f"✗ Row {row_num}: Database error: {e}")
            skipped_fk_errors += 1
            continue
    
    # Step 6: Commit and close
    print("\n[6/6] Committing changes...")
    try:
        db.commit()
        print("✓ All changes committed successfully")
    except Exception as e:
        print(f"✗ Error committing changes: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Print summary
    print("\n" + "=" * 70)
    print("IMPORT SUMMARY")
    print("=" * 70)
    print(f"Total rows in Excel:              {total_rows}")
    print(f"Successfully inserted:            {inserted_rows}")
    print(f"Skipped (FK/validation errors):   {skipped_fk_errors}")
    print(f"Skipped (insufficient funds):     {skipped_insufficient_funds}")
    print(f"Total skipped:                    {skipped_fk_errors + skipped_insufficient_funds}")
    print("=" * 70)
    
    success_rate = (inserted_rows / total_rows * 100) if total_rows > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    print("\n✓ Import process completed!\n")


if __name__ == "__main__":
    import_credit_transfers()


## File: scripts\import_credit_transfers_addin.py
------------------------------
"""Application-level insert-ignore ETL for the ``credit_transfers`` table.

Loads new credit transfer records from an Excel workbook and appends them
to PostgreSQL one row at a time inside a single transaction. Unlike the
``*_upsert.py`` scripts in this directory, ``credit_transfers`` has no
business unique constraint — its only key is the auto-incrementing ``id``
— so a native ``INSERT ... ON CONFLICT`` upsert has no conflict target to
key off. Deduplication is therefore done in the application, against an
in-memory set of composite business keys built from the active rows
already in the table:

    (source_employer_code, destination_employer_code,
     contract_tracking_code, fiscal_year, amount)

A row whose composite key is already present — either in the database or
earlier in the same source file — is skipped as a duplicate rather than
inserted again.

Financial safety: before a row is accepted, the source employer's real
balance for the row's fiscal year is checked via
``services.financial_engine.calculate_real_balance`` and the row is
skipped if the balance cannot cover the transfer amount. Each accepted
row is ``session.flush()``-ed (not committed) immediately after
``session.add()`` so that a later row drawing from the *same* source
employer and fiscal year sees the reserved amount from earlier rows in
this run — without this, two individually-affordable rows in one batch
could jointly overdraw the source employer's balance. ``flush`` keeps
everything inside the same open transaction, so a single
``session.commit()`` at the very end (and a full ``session.rollback()``
on any exception) still governs the whole run, per the transaction-safety
requirement.

Usage
-----
    python scripts/import_credit_transfers_addin.py
"""

from __future__ import annotations

import io
import logging
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from models.contract import Contract  # noqa: E402
from models.employer import Employer  # noqa: E402
from models.transfer import CreditTransfer  # noqa: E402
from services.financial_engine import calculate_real_balance  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("import_credit_transfers_addin")

SOURCE_EXCEL_PATH = PROJECT_ROOT / "data" / "CreditTransfer_Add_In.xlsx"

# Static Persian Excel header -> ORM/DB column name. The fiscal-year column
# is intentionally excluded here since its header embeds a year and varies
# between files (e.g. "انتقال از محل 1402سال مالی"); it is located
# separately via FISCAL_YEAR_COLUMN_HINT.
COLUMN_MAPPING: dict[str, str] = {
    "شماره طبقه بندی شرکت مبدأ": "source_employer_code",
    "شماره طبقه بندی شرکت مقصد": "destination_employer_code",
    "کارگزار قرارداد": "broker_name",
    "مبلغ انتقال (ریال)": "amount",
    "کد رهگیری قرارداد": "contract_tracking_code",
}

FISCAL_YEAR_COLUMN_HINT = re.compile("انتقال از محل")
# Fallback: a 4-digit Jalali-looking year (13xx/14xx) embedded in the
# column header itself, used only if the cell value under that column is
# blank for a given row.
YEAR_IN_HEADER_PATTERN = re.compile(r"(1[34]\d{2})")


class RowSkipped(Exception):
    """Raised internally when a row cannot be converted to a valid record.

    Attributes
    ----------
    reason : str
        One of ``"invalid_data"``, ``"fk_error"``, ``"duplicate"``, or
        ``"insufficient_funds"``, used to route the row into the correct
        summary counter.
    """

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def load_source_dataframe(excel_path: Path) -> pd.DataFrame:
    """Read the source workbook into a DataFrame.

    Args:
        excel_path: Absolute path to the credit transfer Excel workbook.

    Returns:
        The raw, unmodified worksheet contents.

    Raises:
        FileNotFoundError: If ``excel_path`` does not exist.
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Source Excel file not found: {excel_path}")

    dataframe = pd.read_excel(excel_path, engine="openpyxl")
    logger.info("Loaded %d rows from %s", len(dataframe), excel_path.name)
    return dataframe


def find_fiscal_year_column(columns: list[str]) -> str:
    """Locate the dynamically-named fiscal-year column.

    Args:
        columns: The source DataFrame's column headers.

    Returns:
        The matching column name.

    Raises:
        ValueError: If no column header contains "انتقال از محل".
    """
    for column in columns:
        if FISCAL_YEAR_COLUMN_HINT.search(str(column)):
            return column
    raise ValueError(
        "No column containing 'انتقال از محل' found in the source file; "
        f"available columns: {list(columns)}"
    )


def _clean_optional_text(value: Any) -> str | None:
    """Normalize an optional Excel cell to a stripped string or ``None``."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _strip_numeric_artifact(value: str) -> str:
    """Trim pandas' trailing ``.0`` float artifact from a numeric-looking ID."""
    if value.endswith(".0"):
        return value[:-2]
    return value


def _normalize_code(value: Any) -> str | None:
    """Normalize a classification/tracking code cell to a clean string."""
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    return _strip_numeric_artifact(cleaned)


def _clean_amount(value: Any) -> int | None:
    """Parse a Rial amount cell into a positive integer, or ``None``."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        amount = int(value)
    else:
        cleaned = str(value).replace(",", "").replace(".", "").strip()
        if not cleaned:
            return None
        try:
            amount = int(float(cleaned))
        except ValueError:
            return None
    return amount if amount > 0 else None


def _resolve_fiscal_year(row: pd.Series, fiscal_year_column: str) -> int | None:
    """Resolve the row's fiscal year from its cell, falling back to the header.

    Args:
        row: A single row from the source DataFrame.
        fiscal_year_column: The column name located by
            :func:`find_fiscal_year_column`.

    Returns:
        The fiscal year as an integer, or ``None`` if it cannot be
        determined from either the cell value or the column header.
    """
    raw_value = row.get(fiscal_year_column)
    if not pd.isna(raw_value):
        try:
            return int(float(raw_value))
        except (TypeError, ValueError):
            pass

    header_match = YEAR_IN_HEADER_PATTERN.search(str(fiscal_year_column))
    if header_match:
        return int(header_match.group(1))
    return None


def build_active_employer_codes(session: Session) -> set[str]:
    """Load the set of active employer classification codes."""
    rows = (
        session.query(Employer.classification_code)
        .filter(Employer.is_deleted == False)  # noqa: E712
        .all()
    )
    codes = {code for (code,) in rows}
    logger.info("Loaded %d active employer codes.", len(codes))
    return codes


def build_active_contract_codes(session: Session) -> set[str]:
    """Load the set of active contract tracking codes."""
    rows = (
        session.query(Contract.tracking_code)
        .filter(Contract.is_deleted == False)  # noqa: E712
        .all()
    )
    codes = {code for (code,) in rows}
    logger.info("Loaded %d active contract tracking codes.", len(codes))
    return codes


def build_existing_transfer_keys(session: Session) -> set[tuple]:
    """Load composite business keys for every active credit transfer.

    Returns:
        A set of ``(source_employer_code, destination_employer_code,
        contract_tracking_code, fiscal_year, amount)`` tuples, with
        ``amount`` normalized to ``int`` to match the cleaned Excel values.
    """
    rows = (
        session.query(
            CreditTransfer.source_employer_code,
            CreditTransfer.destination_employer_code,
            CreditTransfer.contract_tracking_code,
            CreditTransfer.fiscal_year,
            CreditTransfer.amount,
        )
        .filter(CreditTransfer.is_deleted == False)  # noqa: E712
        .all()
    )
    keys = {
        (source, destination, contract_code, fiscal_year, int(amount))
        for source, destination, contract_code, fiscal_year, amount in rows
    }
    logger.info("Loaded %d existing credit transfer composite keys.", len(keys))
    return keys


def parse_row_fields(row: pd.Series, fiscal_year_column: str) -> dict[str, Any]:
    """Clean one Excel row into candidate ``credit_transfers`` field values.

    Args:
        row: A single row from the source DataFrame.
        fiscal_year_column: The dynamically-located fiscal-year column.

    Returns:
        A dict with cleaned ``source_employer_code``,
        ``destination_employer_code``, ``broker_name``, ``fiscal_year``,
        ``amount``, and ``contract_tracking_code`` values.

    Raises:
        RowSkipped: If any required field is missing or malformed.
    """
    source_employer_code = _normalize_code(row.get("شماره طبقه بندی شرکت مبدأ"))
    if source_employer_code is None:
        raise RowSkipped("invalid_data", "Missing source_employer_code.")

    destination_employer_code = _normalize_code(
        row.get("شماره طبقه بندی شرکت مقصد")
    )
    if destination_employer_code is None:
        raise RowSkipped("invalid_data", "Missing destination_employer_code.")

    contract_tracking_code = _normalize_code(row.get("کد رهگیری قرارداد"))
    if contract_tracking_code is None:
        raise RowSkipped("invalid_data", "Missing contract_tracking_code.")

    fiscal_year = _resolve_fiscal_year(row, fiscal_year_column)
    if fiscal_year is None:
        raise RowSkipped(
            "invalid_data",
            f"Could not determine fiscal_year from column "
            f"'{fiscal_year_column}' or its value.",
        )

    amount = _clean_amount(row.get("مبلغ انتقال (ریال)"))
    if amount is None:
        raise RowSkipped(
            "invalid_data",
            f"Missing or non-positive amount: {row.get('مبلغ انتقال (ریال)')!r}.",
        )

    return {
        "source_employer_code": source_employer_code,
        "destination_employer_code": destination_employer_code,
        "broker_name": _clean_optional_text(row.get("کارگزار قرارداد")),
        "fiscal_year": fiscal_year,
        "amount": amount,
        "contract_tracking_code": contract_tracking_code,
    }


def validate_foreign_keys(
    fields: dict[str, Any],
    active_employer_codes: set[str],
    active_contract_codes: set[str],
) -> None:
    """Confirm every referenced employer/contract is active.

    Raises:
        RowSkipped: If the source employer, destination employer, or
            contract is not an active record.
    """
    if fields["source_employer_code"] not in active_employer_codes:
        raise RowSkipped(
            "fk_error",
            f"Source employer '{fields['source_employer_code']}' not found "
            "among active employers.",
        )
    if fields["destination_employer_code"] not in active_employer_codes:
        raise RowSkipped(
            "fk_error",
            f"Destination employer '{fields['destination_employer_code']}' "
            "not found among active employers.",
        )
    if fields["contract_tracking_code"] not in active_contract_codes:
        raise RowSkipped(
            "fk_error",
            f"Contract '{fields['contract_tracking_code']}' not found "
            "among active contracts.",
        )


def composite_key(fields: dict[str, Any]) -> tuple:
    """Build the composite business key used for insert-ignore deduplication."""
    return (
        fields["source_employer_code"],
        fields["destination_employer_code"],
        fields["contract_tracking_code"],
        fields["fiscal_year"],
        fields["amount"],
    )


def run_import() -> None:
    """Execute the end-to-end insert-ignore import and print a final summary."""
    try:
        dataframe = load_source_dataframe(SOURCE_EXCEL_PATH)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return

    try:
        fiscal_year_column = find_fiscal_year_column(list(dataframe.columns))
    except ValueError as exc:
        logger.error(str(exc))
        return
    logger.info("Resolved fiscal-year column: '%s'", fiscal_year_column)

    session = SessionLocal()

    skip_counts = {
        "invalid_data": 0,
        "fk_error": 0,
        "duplicate": 0,
        "insufficient_funds": 0,
    }
    inserted_count = 0
    total_rows = len(dataframe)

    try:
        active_employer_codes = build_active_employer_codes(session)
        active_contract_codes = build_active_contract_codes(session)
        existing_keys = build_existing_transfer_keys(session)

        for index, row in dataframe.iterrows():
            excel_row_number = index + 2  # 1-indexed plus header row offset.
            try:
                fields = parse_row_fields(row, fiscal_year_column)
                validate_foreign_keys(
                    fields, active_employer_codes, active_contract_codes
                )

                key = composite_key(fields)
                if key in existing_keys:
                    raise RowSkipped(
                        "duplicate",
                        f"Composite key {key} already exists.",
                    )

                current_balance = calculate_real_balance(
                    session,
                    fields["source_employer_code"],
                    fields["fiscal_year"],
                )
                if current_balance < fields["amount"]:
                    raise RowSkipped(
                        "insufficient_funds",
                        "INSUFFICIENT FUNDS for employer "
                        f"'{fields['source_employer_code']}' in fiscal year "
                        f"{fields['fiscal_year']}: current balance "
                        f"{current_balance:,.0f} Rials, requested transfer "
                        f"{fields['amount']:,.0f} Rials "
                        f"(deficit {fields['amount'] - current_balance:,.0f}).",
                    )

            except RowSkipped as exc:
                skip_counts[exc.reason] += 1
                logger.warning("Row %d skipped: %s", excel_row_number, exc)
                continue

            transfer = CreditTransfer(
                source_employer_code=fields["source_employer_code"],
                destination_employer_code=fields["destination_employer_code"],
                broker_name=fields["broker_name"],
                fiscal_year=fields["fiscal_year"],
                amount=fields["amount"],
                contract_tracking_code=fields["contract_tracking_code"],
                is_deleted=False,
            )
            session.add(transfer)
            # Flush (not commit) so a later row against the same source
            # employer/fiscal year sees this reserved amount in its own
            # balance check, and so an in-file duplicate of this exact row
            # is caught by the composite-key set below.
            session.flush()
            existing_keys.add(key)
            inserted_count += 1
            logger.info(
                "Row %d accepted: %s -> %s, contract %s, fiscal_year %s, "
                "amount %s Rials.",
                excel_row_number,
                fields["source_employer_code"],
                fields["destination_employer_code"],
                fields["contract_tracking_code"],
                fields["fiscal_year"],
                f"{fields['amount']:,.0f}",
            )

        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Import failed, transaction rolled back: %s", exc)
        return
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("CREDIT TRANSFER APPEND SUMMARY")
    print("=" * 60)
    print(f"Source rows read:                 {total_rows}")
    print(f"Inserted:                         {inserted_count}")
    print(f"Skipped (duplicate):               {skip_counts['duplicate']}")
    print(f"Skipped (FK error):                {skip_counts['fk_error']}")
    print(f"Skipped (insufficient funds):      {skip_counts['insufficient_funds']}")
    print(f"Skipped (other invalid data):       {skip_counts['invalid_data']}")
    print("=" * 60)


if __name__ == "__main__":
    run_import()


## File: scripts\import_deposits.py
------------------------------
import os
import sys
from pathlib import Path
from datetime import date
import shutil

import pandas as pd

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, SessionLocal, engine
from models.employer import Employer
from models.deposits import AnnualMandate, DepositReceipt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "Budget.xlsx"
TEMP_FILE_PATH = Path("C:/Temp/Budget_temp.xlsx")

# Unit conversion: Excel values are in Billion Rials, convert to base Rials
BILLION = 1_000_000_000


def normalize_code(value):
    """Normalize employer code by removing .0 suffix from numeric strings."""
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.endswith(".0"):
        return value[:-2]
    return value


def extract_year_from_column(col_name):
    """Extract integer year from Persian column names like 'سال 1398' or 'واریزی 1402'."""
    parts = col_name.split()
    for part in parts:
        if part.isdigit():
            return int(part)
    raise ValueError(f"Could not extract year from column: {col_name}")


def load_and_transform_budgets(file_path: Path):
    """Load both sheets and transform from wide to long format."""
    
    print(f"Reading Excel file: {file_path}")
    
    # Read Assigned_Budgets sheet
    assigned_df = pd.read_excel(file_path, sheet_name='Assigned_Budgets', engine='openpyxl')
    print(f"Loaded {len(assigned_df)} rows from Assigned_Budgets sheet")
    print(f"Column count: {len(assigned_df.columns)}")
    
    # Read Deposit_Budget sheet
    deposit_df = pd.read_excel(file_path, sheet_name='Deposit_Budget', engine='openpyxl')
    print(f"Loaded {len(deposit_df)} rows from Deposit_Budget sheet")
    print(f"Column count: {len(deposit_df.columns)}")
    
    # Transform Assigned_Budgets: wide to long
    code_col = 'شماره طبقه بندی'
    year_cols_assigned = [col for col in assigned_df.columns if col.startswith('سال')]
    
    assigned_long = pd.melt(
        assigned_df,
        id_vars=[code_col],
        value_vars=year_cols_assigned,
        var_name='year_column',
        value_name='mandated_amount'
    )
    assigned_long['fiscal_year'] = assigned_long['year_column'].apply(extract_year_from_column)
    assigned_long['employer_code'] = assigned_long[code_col].apply(normalize_code)
    assigned_long = assigned_long[['employer_code', 'fiscal_year', 'mandated_amount']]
    assigned_long['mandated_amount'] = pd.to_numeric(assigned_long['mandated_amount'], errors='coerce').fillna(0)
    
    # CRITICAL: Convert from Billion Rials to base Rials
    assigned_long['mandated_amount'] = assigned_long['mandated_amount'] * BILLION
    
    print(f"Transformed Assigned_Budgets to {len(assigned_long)} long-format rows (scaled to base Rials)")
    
    # Transform Deposit_Budget: wide to long
    year_cols_deposit = [col for col in deposit_df.columns if col.startswith('واریزی')]
    
    deposit_long = pd.melt(
        deposit_df,
        id_vars=[code_col],
        value_vars=year_cols_deposit,
        var_name='year_column',
        value_name='deposited_amount'
    )
    deposit_long['fiscal_year'] = deposit_long['year_column'].apply(extract_year_from_column)
    deposit_long['employer_code'] = deposit_long[code_col].apply(normalize_code)
    deposit_long = deposit_long[['employer_code', 'fiscal_year', 'deposited_amount']]
    deposit_long['deposited_amount'] = pd.to_numeric(deposit_long['deposited_amount'], errors='coerce').fillna(0)
    
    # CRITICAL: Convert from Billion Rials to base Rials
    #deposit_long['deposited_amount'] = deposit_long['deposited_amount'] * BILLION
    
    print(f"Transformed Deposit_Budget to {len(deposit_long)} long-format rows (scaled to base Rials)")
    
    # Merge on employer_code and fiscal_year (outer join)
    merged_df = pd.merge(
        assigned_long,
        deposit_long,
        on=['employer_code', 'fiscal_year'],
        how='outer'
    )
    merged_df['mandated_amount'] = merged_df['mandated_amount'].fillna(0)
    merged_df['deposited_amount'] = merged_df['deposited_amount'].fillna(0)
    
    print(f"Merged DataFrame has {len(merged_df)} rows")
    
    return merged_df


def persian_date_to_gregorian(year, month, day):
    """
    Simplified Persian to Gregorian conversion.
    For MVP purposes, we'll use a simple approximation:
    Persian year Y maps roughly to Gregorian year Y+621 or Y+622.
    The last day of Persian year (12/29) is around March 20.
    """
    gregorian_year = year + 621
    return date(gregorian_year, 3, 20)


def import_deposits(file_path: Path = EXCEL_FILE_PATH):
    """Main ETL function: Extract, Transform, Load deposit data."""
    
    # Drop existing tables in correct order (child first, then parent)
    print("Dropping existing deposit tables...")
    DepositReceipt.__table__.drop(engine, checkfirst=True)
    AnnualMandate.__table__.drop(engine, checkfirst=True)
    print("Tables dropped successfully.")
    
    # Recreate schema
    print("Recreating deposit tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    # Use temp file if original is locked - check before attempting to use
    if TEMP_FILE_PATH.exists():
        actual_file = TEMP_FILE_PATH
        print(f"Using temp file: {actual_file}")
    else:
        actual_file = file_path
        print(f"Using original file: {actual_file}")
    
    # Load and transform data
    merged_df = load_and_transform_budgets(actual_file)
    
    # Get valid employer codes from database
    db = SessionLocal()
    try:
        valid_codes = {emp.classification_code for emp in db.query(Employer.classification_code).all()}
        print(f"Found {len(valid_codes)} valid employer codes in database")
        
        mandates_added = 0
        receipts_added = 0
        skipped_missing_employer = 0
        
        for idx, row in merged_df.iterrows():
            employer_code = row['employer_code']
            fiscal_year = int(row['fiscal_year'])
            mandated_amount = float(row['mandated_amount'])
            deposited_amount = float(row['deposited_amount'])
            
            # Skip if employer doesn't exist
            if employer_code not in valid_codes:
                if skipped_missing_employer < 5:  # Only log first 5
                    print(f"WARNING: Skipping row {idx} - employer_code '{employer_code}' not found in database")
                skipped_missing_employer += 1
                continue
            
            # Create Annual_Mandate record
            mandate = AnnualMandate(
                employer_code=employer_code,
                fiscal_year=fiscal_year,
                mandated_amount=mandated_amount
            )
            db.add(mandate)
            mandates_added += 1
            
            # Create Deposit_Receipt if deposited_amount > 0
            if deposited_amount > 0:
                deposit_date = persian_date_to_gregorian(fiscal_year, 12, 29)
                receipt = DepositReceipt(
                    employer_code=employer_code,
                    fiscal_year=fiscal_year,
                    deposit_amount=deposited_amount,
                    deposit_date=deposit_date,
                    description='Historical Aggregated Deposit'
                )
                db.add(receipt)
                receipts_added += 1
        
        # Commit transaction
        db.commit()
        print("\n=== Import Summary ===")
        print(f"Successfully imported {mandates_added} Annual_Mandate records")
        print(f"Successfully imported {receipts_added} Deposit_Receipt records")
        print(f"Skipped {skipped_missing_employer} rows due to missing employer codes")
        print(f"\nNote: All monetary values converted from Billion Rials to base Rials (×{BILLION:,})")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: Database transaction failed. Rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_deposits()


## File: scripts\import_employers.py
------------------------------
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from core.database import Base, SessionLocal, engine
from models.employer import Employer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "Employers.xlsx"

COLUMN_MAPPING = {
    "شماره طبقه بندی": "classification_code",
    "نام مشمول": "name",
    "نوع مشمول": "employer_type",
    "شماره طبقه بندی سازمان مادر": "parent_code",
    "استان": "province",
    "عنوان امور": "affairs_category",
    "دستگاه اجرایی بالادست": "upper_organization",
    "وضعیت فعالیت": "status",
}

EMPLOYER_TYPE_MAPPING = {
    "مادر": "Mother",
    "زیرمجموعه": "Subsidiary",
    "مستقل": "Independent",
}

STATUS_MAPPING = {
    "فعال": "Active",
    "غیرفعال": "Inactive",
}

UNKNOWN_REQUIRED_VALUE = "Unknown"


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return str(value).strip()


def normalize_code(value):
    value = clean_value(value)
    if value is None:
        return None
    if value.endswith(".0"):
        return value[:-2]
    return value


def normalize_employer_type(value):
    value = clean_value(value)
    return EMPLOYER_TYPE_MAPPING.get(value, value)


def normalize_status(value):
    value = clean_value(value)
    if value is None:
        return "Active"
    return STATUS_MAPPING.get(value, value)


def load_employers_dataframe(file_path: Path) -> pd.DataFrame:
    df = pd.read_excel(file_path, engine="openpyxl")
    missing_columns = set(COLUMN_MAPPING) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing Excel columns: {sorted(missing_columns)}")
    df = df.rename(columns=COLUMN_MAPPING)
    return df.where(pd.notnull(df), None)


def build_employer(row) -> Employer:
    classification_code = normalize_code(row["classification_code"])
    if classification_code is None:
        raise ValueError("classification_code is required")

    return Employer(
        classification_code=classification_code,
        name=clean_value(row["name"]) or UNKNOWN_REQUIRED_VALUE,
        employer_type=normalize_employer_type(row["employer_type"]),
        parent_code=normalize_code(row["parent_code"]),
        province=clean_value(row["province"]) or UNKNOWN_REQUIRED_VALUE,
        affairs_category=clean_value(row["affairs_category"]),
        upper_organization=clean_value(row["upper_organization"]) or UNKNOWN_REQUIRED_VALUE,
        status=normalize_status(row["status"]),
    )


def import_employers(file_path: Path = EXCEL_FILE_PATH) -> None:
    # Force drop the table and all its dependents
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS employers CASCADE"))
    Base.metadata.create_all(bind=engine)

    print(f"Reading Excel file: {file_path}")
    df = load_employers_dataframe(file_path)
    print(f"Loaded {len(df)} rows from Excel.")

    db = SessionLocal()
    records_added = 0
    duplicates_skipped = 0

    try:
        for index, row in df.iterrows():
            employer = build_employer(row)

            existing_employer = (
                db.query(Employer)
                .filter_by(classification_code=employer.classification_code)
                .first()
            )
            if existing_employer:
                duplicates_skipped += 1
                print(f"Skipping duplicate: {employer.classification_code}")
                continue

            db.add(employer)
            records_added += 1

        db.commit()
        print("Import committed successfully.")
        print(f"Successfully imported {records_added} new employers.")
        print(f"Skipped {duplicates_skipped} existing employers.")
    except Exception:
        db.rollback()
        print("Database transaction failed. Rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_employers()


## File: scripts\import_payments.py
------------------------------
import sys
import os
from datetime import datetime, date

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.date_helper import parse_strict_jalali_date
from core.database import engine, Base
from models.payment import Payment
from models.contract import Contract


def parse_jalali_date(date_str):
    """Parse a Jalali date strictly and return a Gregorian date."""
    if pd.isna(date_str) or date_str == "" or date_str is None:
        return None

    try:
        return parse_strict_jalali_date(str(date_str))
    except (TypeError, ValueError):
        return None


def clean_numeric(value):
    """Remove commas from numeric strings and convert to int."""
    if pd.isna(value):
        return 0
    
    try:
        # Convert to string, remove commas, then to int
        cleaned = str(value).replace(',', '').strip()
        return int(float(cleaned))
    except (ValueError, AttributeError):
        return 0


def main():
    print("Starting Payments import...")
    
    # Read Excel file
    print("\n1. Reading Excel file...")
    df = pd.read_excel('data/Payments.xlsx')
    print(f"   Loaded {len(df)} rows from Excel")
    
    # Display column names for verification
    print(f"\n   Columns found: {df.columns.tolist()}")
    
    # Expected Persian headers
    expected_cols = [
        'سری پرداخت',
        'کد رهگیری پرداخت', 
        'کد رهگیری',
        'مبلغ پرداختی(ریال)',
        'شماره نامه ابلاغ',
        'تاریخ ابلاغ',
        'سال پرداخت',
        'پرداخت از محل سال مالی'
    ]
    
    # Verify all expected columns exist
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        print(f"\n   WARNING: Missing columns: {missing_cols}")
        return
    
    # Drop table and recreate
    print("\n2. Dropping existing payments table...")
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS payments CASCADE"))
    
    print("   Creating fresh payments table...")
    Base.metadata.create_all(bind=engine, tables=[Payment.__table__])
    
    # Fetch valid contract tracking codes
    print("\n3. Fetching valid contract tracking codes...")
    session = Session(bind=engine)
    try:
        valid_contracts = set(
            session.query(Contract.tracking_code)
            .filter(Contract.is_deleted == False)
            .all()
        )
        valid_contracts = {code[0] for code in valid_contracts}
        print(f"   Found {len(valid_contracts)} valid contracts")
    finally:
        session.close()
    
    # Process payments
    print("\n4. Processing payment records...")
    session = Session(bind=engine)
    
    inserted_count = 0
    skipped_count = 0
    skipped_reasons = []
    
    try:
        for idx, row in df.iterrows():
            # Extract values
            tracking_code = str(row['کد رهگیری پرداخت']).strip() if pd.notna(row['کد رهگیری پرداخت']) else None
            contract_tracking_code = str(row['کد رهگیری']).strip() if pd.notna(row['کد رهگیری']) else None
            series = str(row['سری پرداخت']).strip() if pd.notna(row['سری پرداخت']) else None
            amount = clean_numeric(row['مبلغ پرداختی(ریال)'])
            notification_letter_number = str(row['شماره نامه ابلاغ']).strip() if pd.notna(row['شماره نامه ابلاغ']) else None
            notification_date = parse_jalali_date(row['تاریخ ابلاغ'])
            payment_year = int(row['سال پرداخت']) if pd.notna(row['سال پرداخت']) else None
            funding_year = int(row['پرداخت از محل سال مالی']) if pd.notna(row['پرداخت از محل سال مالی']) else None
            
            # Validate required fields
            if not tracking_code:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Missing tracking_code")
                continue
            
            if not contract_tracking_code:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Missing contract_tracking_code")
                continue
            
            # Validate FK integrity
            if contract_tracking_code not in valid_contracts:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Contract '{contract_tracking_code}' not found")
                continue
            
            if not payment_year or not funding_year:
                skipped_count += 1
                skipped_reasons.append(f"Row {idx+2}: Missing payment_year or funding_year")
                continue
            
            # Create Payment instance
            payment = Payment(
                tracking_code=tracking_code,
                contract_tracking_code=contract_tracking_code,
                series=series,
                amount=amount,
                notification_letter_number=notification_letter_number,
                notification_date=notification_date,
                payment_year=payment_year,
                funding_year=funding_year,
                attachment_path=None
            )
            
            session.add(payment)
            inserted_count += 1
        
        # Commit all changes
        session.commit()
        print(f"\n✓ Successfully inserted {inserted_count} payments")
        
        if skipped_count > 0:
            print(f"\n⚠ Skipped {skipped_count} rows due to validation errors:")
            for reason in skipped_reasons[:10]:  # Show first 10
                print(f"   - {reason}")
            if len(skipped_reasons) > 10:
                print(f"   ... and {len(skipped_reasons) - 10} more")
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error during import: {e}")
        raise
    finally:
        session.close()
    
    print("\n" + "="*50)
    print("Payment import completed!")
    print(f"Total rows processed: {len(df)}")
    print(f"Successfully inserted: {inserted_count}")
    print(f"Skipped: {skipped_count}")
    print("="*50)


if __name__ == '__main__':
    main()


## File: scripts\import_payments_upsert.py
------------------------------
"""Idempotent upsert ETL for the ``payments`` table.

Loads payment records from an Excel workbook and writes them to
PostgreSQL using a single native ``INSERT ... ON CONFLICT (tracking_code)
DO UPDATE`` statement (via ``sqlalchemy.dialects.postgresql.insert``). Like
the other ``*_upsert.py`` scripts in this directory, this script never
drops the table and never performs an application-level "SELECT then
INSERT/UPDATE" check for the conflict target — PostgreSQL resolves the
insert-vs-update race atomically.

Missing NOT NULL columns: the source file has no ``payment_date``,
``execution_year``, or ``payment_type`` columns, all of which are
``nullable=False`` on ``Payment``. Per the task's fallback rules:

* ``payment_date``  <- the row's parsed ``notification_date`` (``تاریخ
  ابلاغ``); if that fails to parse, the row is skipped entirely, since
  there is no other date to fall back to.
* ``execution_year`` <- ``int(funding_year)`` (``پرداخت از محل سال مالی``).
* ``payment_type``   <- the fixed placeholder ``"نامشخص"``.

Financial warning (FR-20): before a row is accepted, its projected balance
is checked via ``services.financial_engine.calculate_real_balance``, but a
negative projection only logs a warning and increments a counter — it
never skips the row, matching the system-wide FR-20 rule that negative
balances warn but do not block. Balances are tracked as a running,
in-memory projection per ``(employer_code, funding_year)`` across the
whole batch (mirroring ``api/v1/endpoints/payments.py``'s
``bulk_submit_payments``), so a second payment in this same file against
the same employer and funding year is checked against the balance *after*
the first payment's amount has been provisionally subtracted, not against
the stale pre-batch database balance.

Usage
-----
    python scripts/import_payments_upsert.py
"""

from __future__ import annotations

import io
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from core.date_helper import parse_strict_jalali_date  # noqa: E402
from models.contract import Contract  # noqa: E402
from models.payment import Payment  # noqa: E402
from services.financial_engine import calculate_real_balance  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("import_payments_upsert")

SOURCE_EXCEL_PATH = PROJECT_ROOT / "data" / "Payments_Add_In.xlsx"

PAYMENT_TYPE_PLACEHOLDER = "نامشخص"

# Columns refreshed on conflict. ``is_deleted`` is appended separately below
# so a soft-deleted row is always restored, regardless of the source value.
UPDATABLE_COLUMNS = (
    "contract_tracking_code",
    "series",
    "amount",
    "notification_letter_number",
    "notification_date",
    "payment_year",
    "funding_year",
    "payment_date",
    "execution_year",
    "payment_type",
)


class RowSkipped(Exception):
    """Raised internally when a row cannot be converted to a valid record.

    Attributes
    ----------
    reason : str
        One of ``"missing_fk"``, ``"bad_date"``, or ``"invalid_data"``,
        used to route the row into the correct summary counter.
    """

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def load_source_dataframe(excel_path: Path) -> pd.DataFrame:
    """Read the source workbook into a DataFrame.

    Args:
        excel_path: Absolute path to the payments Excel workbook.

    Returns:
        The raw, unmodified worksheet contents.

    Raises:
        FileNotFoundError: If ``excel_path`` does not exist.
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Source Excel file not found: {excel_path}")

    dataframe = pd.read_excel(excel_path, engine="openpyxl")
    logger.info("Loaded %d rows from %s", len(dataframe), excel_path.name)
    return dataframe


def _clean_optional_text(value: Any) -> str | None:
    """Normalize an optional Excel cell to a stripped string or ``None``."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _strip_numeric_artifact(value: str) -> str:
    """Trim pandas' trailing ``.0`` float artifact from a numeric-looking ID."""
    if value.endswith(".0"):
        return value[:-2]
    return value


def _normalize_code(value: Any) -> str | None:
    """Normalize a tracking-code cell to a clean string."""
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    return _strip_numeric_artifact(cleaned)


def _clean_amount(value: Any) -> int | None:
    """Parse a Rial amount cell into a positive integer, or ``None``."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        amount = int(value)
    else:
        cleaned = str(value).replace(",", "").strip()
        if not cleaned:
            return None
        try:
            amount = int(float(cleaned))
        except ValueError:
            return None
    return amount if amount > 0 else None


def _clean_year(value: Any) -> int | None:
    """Parse a fiscal-year cell into an integer, or ``None``."""
    if pd.isna(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def build_valid_contracts(session: Session) -> dict[str, str]:
    """Build a ``{contract_tracking_code: employer_code}`` lookup map.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from every active contract's tracking code to its
        linked employer's classification code.
    """
    rows = (
        session.query(Contract.tracking_code, Contract.employer_code)
        .filter(Contract.is_deleted == False)  # noqa: E712
        .all()
    )
    lookup = {tracking_code: employer_code for tracking_code, employer_code in rows}
    logger.info("Loaded %d active contract tracking codes.", len(lookup))
    return lookup


def build_existing_payment_amounts(session: Session) -> dict[str, float]:
    """Build a ``{tracking_code: amount}`` map of every active payment.

    Used by :func:`apply_balance_warnings` to avoid double-counting a
    payment that already exists in the database: ``calculate_real_balance``
    already reflects committed payments, so re-subtracting an existing
    row's amount on every re-run (an ``ON CONFLICT DO UPDATE``, not a new
    insert) would understate the balance more each time the script runs
    against unchanged data.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from every active payment's tracking code to its current
        ``amount`` (as ``float``, to match ``calculate_real_balance``'s
        return type).
    """
    rows = (
        session.query(Payment.tracking_code, Payment.amount)
        .filter(Payment.is_deleted == False)  # noqa: E712
        .all()
    )
    return {tracking_code: float(amount) for tracking_code, amount in rows}


def parse_row_fields(row: pd.Series, valid_contracts: dict[str, str]) -> dict[str, Any]:
    """Clean and validate one Excel row into candidate ``payments`` fields.

    Args:
        row: A single row from the source DataFrame.
        valid_contracts: Mapping built by :func:`build_valid_contracts`.

    Returns:
        A dict with every cleaned field plus the resolved ``employer_code``
        (kept alongside the record for the FR-20 balance check, not itself
        a ``payments`` column).

    Raises:
        RowSkipped: If the contract reference is missing/invalid, the
            notification date cannot be parsed, or another required field
            is missing/malformed.
    """
    tracking_code = _normalize_code(row.get("کد رهگیری پرداخت"))
    if tracking_code is None:
        raise RowSkipped("invalid_data", "Missing tracking_code.")

    contract_tracking_code = _normalize_code(row.get("کد رهگیری"))
    if contract_tracking_code is None:
        raise RowSkipped(
            "missing_fk",
            f"Missing contract_tracking_code for payment '{tracking_code}'.",
        )
    employer_code = valid_contracts.get(contract_tracking_code)
    if employer_code is None:
        raise RowSkipped(
            "missing_fk",
            f"Contract '{contract_tracking_code}' not found among active "
            "contracts.",
        )

    raw_notification_date = row.get("تاریخ ابلاغ")
    if pd.isna(raw_notification_date):
        raise RowSkipped(
            "bad_date",
            f"Missing notification_date for payment '{tracking_code}'.",
        )
    try:
        notification_date: date = parse_strict_jalali_date(str(raw_notification_date))
    except (TypeError, ValueError) as exc:
        raise RowSkipped(
            "bad_date",
            f"Invalid Jalali notification_date "
            f"'{raw_notification_date}' for payment '{tracking_code}': {exc}",
        ) from exc

    amount = _clean_amount(row.get("مبلغ پرداختی(ریال)"))
    if amount is None:
        raise RowSkipped(
            "invalid_data",
            f"Missing or non-positive amount for payment '{tracking_code}'.",
        )

    funding_year = _clean_year(row.get("پرداخت از محل سال مالی"))
    if funding_year is None:
        raise RowSkipped(
            "invalid_data",
            f"Missing or non-numeric funding_year for payment "
            f"'{tracking_code}'.",
        )

    payment_year = _clean_year(row.get("سال پرداخت"))

    return {
        "tracking_code": tracking_code,
        "contract_tracking_code": contract_tracking_code,
        "series": _clean_optional_text(row.get("سری پرداخت")),
        "amount": amount,
        "notification_letter_number": _clean_optional_text(
            row.get("شماره نامه ابلاغ")
        ),
        "notification_date": notification_date,
        "payment_year": payment_year,
        "funding_year": funding_year,
        # Fallbacks for columns absent from the source file but NOT NULL
        # on the model.
        "payment_date": notification_date,
        "execution_year": funding_year,
        "payment_type": PAYMENT_TYPE_PLACEHOLDER,
        "is_deleted": False,
        # Not a payments column; carried through for the FR-20 check below.
        "_employer_code": employer_code,
    }


def transform_dataframe(
    dataframe: pd.DataFrame,
    valid_contracts: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Convert every Excel row to sanitized upsert records.

    Duplicate ``tracking_code`` values within the source file are
    collapsed to the last occurrence, since PostgreSQL rejects an
    ``ON CONFLICT`` batch that targets the same conflict key twice.

    Args:
        dataframe: The raw source worksheet.
        valid_contracts: Mapping built by :func:`build_valid_contracts`.

    Returns:
        A tuple of (deduplicated records ready for upsert, skip counters
        keyed by reason).
    """
    records_by_tracking_code: dict[str, dict[str, Any]] = {}
    skip_counts = {"missing_fk": 0, "bad_date": 0, "invalid_data": 0}

    for index, row in dataframe.iterrows():
        excel_row_number = index + 2  # 1-indexed plus header row offset.
        try:
            record = parse_row_fields(row, valid_contracts)
        except RowSkipped as exc:
            skip_counts[exc.reason] += 1
            logger.warning("Row %d skipped: %s", excel_row_number, exc)
            continue

        records_by_tracking_code[record["tracking_code"]] = record

    return list(records_by_tracking_code.values()), skip_counts


def apply_balance_warnings(
    session: Session,
    records: list[dict[str, Any]],
    existing_payment_amounts: dict[str, float],
) -> list[str]:
    """Project each payment's impact on its employer's balance (FR-20).

    A negative projected balance never removes the row from ``records`` —
    it only produces a warning message and is logged. Balances are tracked
    as a running total per ``(employer_code, funding_year)`` across
    ``records`` in order, so multiple payments in this file against the
    same employer/year are checked cumulatively rather than each against
    the stale pre-batch database balance.

    ``calculate_real_balance`` already sums every active payment in the
    database, including ones this same run is about to *update* (not
    insert) via ``ON CONFLICT``. Before subtracting such a row's amount,
    its previously-committed amount is added back first, so re-running
    this script against unchanged data doesn't double-count an existing
    payment and manufacture a growing deficit on every run.

    Args:
        session: Active SQLAlchemy session.
        records: Sanitized rows produced by :func:`transform_dataframe`.
        existing_payment_amounts: Mapping built by
            :func:`build_existing_payment_amounts`.

    Returns:
        Human-readable warning messages, one per payment that projects a
        negative balance.
    """
    running_balances: dict[tuple[str, int], float] = {}
    warnings: list[str] = []

    for record in records:
        employer_code = record["_employer_code"]
        funding_year = record["funding_year"]
        balance_key = (employer_code, funding_year)

        if balance_key not in running_balances:
            running_balances[balance_key] = calculate_real_balance(
                session, employer_code, funding_year
            )

        # Undo this row's own prior contribution (if any) before applying
        # its new amount, so an update of an unchanged existing row nets
        # to zero instead of being subtracted a second time.
        running_balances[balance_key] += existing_payment_amounts.get(
            record["tracking_code"], 0.0
        )
        running_balances[balance_key] -= record["amount"]
        if running_balances[balance_key] < 0:
            message = (
                "FR-20 WARNING: payment "
                f"'{record['tracking_code']}' projects a negative balance "
                f"for employer '{employer_code}', funding year "
                f"{funding_year}: {running_balances[balance_key]:,.0f} "
                "Rials (deficit "
                f"{-running_balances[balance_key]:,.0f} Rials)."
            )
            warnings.append(message)
            logger.warning(message)

    return warnings


def build_upsert_statement(records: list[dict[str, Any]]):
    """Build the native PostgreSQL ``INSERT ... ON CONFLICT DO UPDATE`` statement.

    All rows are batched into a single statement so the entire import
    commits atomically and PostgreSQL — not the application — resolves the
    insert-vs-update race for each ``tracking_code``.

    Args:
        records: Sanitized rows produced by :func:`transform_dataframe`.
            The internal ``_employer_code`` key is stripped before the
            statement is built, since it is not a ``payments`` column.

    Returns:
        An executable SQLAlchemy ``Insert`` construct with the upsert
        clause attached.
    """
    payment_columns = {
        column.name for column in Payment.__table__.columns
    }
    clean_records = [
        {key: value for key, value in record.items() if key in payment_columns}
        for record in records
    ]

    insert_statement = pg_insert(Payment).values(clean_records)

    update_columns = {
        column: getattr(insert_statement.excluded, column)
        for column in UPDATABLE_COLUMNS
    }
    # Always restore a previously soft-deleted record on re-import.
    update_columns["is_deleted"] = False

    return insert_statement.on_conflict_do_update(
        index_elements=[Payment.tracking_code],
        set_=update_columns,
    )


def run_upsert_import() -> None:
    """Execute the end-to-end upsert import and print a final summary."""
    try:
        dataframe = load_source_dataframe(SOURCE_EXCEL_PATH)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return

    session = SessionLocal()
    try:
        valid_contracts = build_valid_contracts(session)
        existing_payment_amounts = build_existing_payment_amounts(session)
    except SQLAlchemyError as exc:
        logger.error("Failed to load lookup data: %s", exc)
        session.close()
        return

    records, skip_counts = transform_dataframe(dataframe, valid_contracts)

    if not records:
        logger.warning("No valid rows to upsert; nothing was written.")
        session.close()
        return

    try:
        warnings = apply_balance_warnings(session, records, existing_payment_amounts)
        statement = build_upsert_statement(records)
        result = session.execute(statement)
        session.commit()
        processed_count = result.rowcount
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Upsert failed, transaction rolled back: %s", exc)
        return
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("PAYMENT UPSERT SUMMARY")
    print("=" * 60)
    print(f"Source rows read:                 {len(dataframe)}")
    print(f"Skipped (missing/invalid FK):      {skip_counts['missing_fk']}")
    print(f"Skipped (invalid date):            {skip_counts['bad_date']}")
    print(f"Skipped (other invalid data):      {skip_counts['invalid_data']}")
    print(f"Rows processed (upsert):           {processed_count}")
    print(f"FR-20 negative-balance warnings:   {len(warnings)}")
    print("=" * 60)


if __name__ == "__main__":
    run_upsert_import()


## File: scripts\import_researchers.py
------------------------------
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base, SessionLocal, engine
from models.researchers import Researcher
from models.university import University
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_FILE_PATH = PROJECT_ROOT / "data" / "Researchers.xlsx"

COLUMN_MAPPING = {
    "کد رهگیری فناور": "tracking_code",
    "کد ملی فناور": "national_code",
    "نام فناور": "first_name",
    "نام خانوادگی فناور": "last_name",
    "تلفن همراه": "mobile",
    "ایمیل": "email",
    "درجه علمی": "academic_rank",
    "شناسه ملی موسسه": "university_id",
    "مدرک تحصیلی": "education_level",
    "نوع فناور": "researcher_type",
    "وضعیت": "status",
}

STATUS_MAPPING = {
    "فعال": "Active",
    "غیرفعال": "Inactive",
}


def clean_value(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value or None


def normalize_status(value):
    value = clean_value(value)
    if value is None:
        return "Active"
    return STATUS_MAPPING.get(value, value)


def load_researchers_dataframe(file_path: Path) -> pd.DataFrame:
    df = pd.read_excel(file_path, engine="openpyxl")
    missing_columns = set(COLUMN_MAPPING) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing Excel columns: {sorted(missing_columns)}")
    df = df.rename(columns=COLUMN_MAPPING)
    return df.where(pd.notnull(df), None)


def build_researcher(row) -> Researcher | None:
    national_code = clean_value(row["national_code"])
    if national_code is None:
        return None

    first_name = clean_value(row["first_name"])
    last_name = clean_value(row["last_name"])

    return Researcher(
        national_code=national_code,
        tracking_code=clean_value(row["tracking_code"]),
        first_name=first_name or "Unknown",
        last_name=last_name or "Unknown",
        full_name=f"{first_name or 'Unknown'} {last_name or 'Unknown'}",
        mobile=clean_value(row["mobile"]),
        email=clean_value(row["email"]),
        academic_rank=clean_value(row["academic_rank"]),
        university_id=clean_value(row["university_id"]),
        education_level=clean_value(row["education_level"]),
        researcher_type=clean_value(row["researcher_type"]),
        status=normalize_status(row["status"]),
    )


def import_researchers(file_path: Path = EXCEL_FILE_PATH) -> None:
    # Force drop the table and all its dependents (e.g., contracts)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS researchers CASCADE"))
    Base.metadata.create_all(bind=engine)

    print(f"Reading Excel file: {file_path}")
    df = load_researchers_dataframe(file_path)
    print(f"Loaded {len(df)} rows from Excel.")

    db = SessionLocal()
    records_added = 0
    missing_national_code_skipped = 0
    invalid_university_skipped = 0
    duplicate_skipped = 0
    seen_national_codes = set()

    try:
        valid_universities = {
            national_id for (national_id,) in db.query(University.national_id).all()
        }
        print(f"Loaded {len(valid_universities)} valid universities for FK checks.")

        for index, row in df.iterrows():
            researcher = build_researcher(row)
            if researcher is None:
                missing_national_code_skipped += 1
                continue

            if researcher.national_code in seen_national_codes:
                duplicate_skipped += 1
                print(f"Row {index + 2}: skipping duplicate national_code {researcher.national_code}")
                continue

            if researcher.university_id not in valid_universities:
                invalid_university_skipped += 1
                print(
                    f"Row {index + 2}: skipping researcher {researcher.national_code}; "
                    f"invalid university_id {researcher.university_id}"
                )
                continue

            db.add(researcher)
            seen_national_codes.add(researcher.national_code)
            records_added += 1

        db.commit()
        print("Import committed successfully.")
        print(f"Successfully imported {records_added} researchers.")
        print(f"Skipped {missing_national_code_skipped} rows without national_code.")
        print(f"Skipped {invalid_university_skipped} rows with invalid university_id.")
        print(f"Skipped {duplicate_skipped} duplicate researchers.")
    except Exception:
        db.rollback()
        print("Database transaction failed. Rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_researchers()


## File: scripts\import_researchers_upsert.py
------------------------------
"""Idempotent upsert ETL for the ``researchers`` table.

Loads researcher (فناور) records from an Excel workbook and writes them to
PostgreSQL using a single native ``INSERT ... ON CONFLICT (national_code)
DO UPDATE`` statement (via ``sqlalchemy.dialects.postgresql.insert``). Like
``scripts/import_universities_upsert.py``, this script never drops the
table and never performs an application-level "SELECT then INSERT/UPDATE"
check for the conflict target — PostgreSQL resolves the insert-vs-update
race atomically.

University resolution: the source file has no ``university_id`` column,
only a free-text institution name (``دانشگاه / محل خدمت``). Before
transforming rows, the full ``{name: national_id}`` mapping is loaded once
from the ``universities`` table (whitespace-stripped on both sides for
comparison) and used to resolve each row's ``university_id``. A row whose
institution name cannot be resolved is skipped and logged as a warning —
``researchers.university_id`` is a required foreign key, so there is no
safe default to fall back to.

Soft-delete interaction: if a ``national_code`` re-appears in the source
file after having been soft-deleted (``is_deleted = True``), the update
clause forces ``is_deleted = False``, restoring the record.

Usage
-----
    python scripts/import_researchers_upsert.py
"""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from models.researchers import Researcher  # noqa: E402
from models.university import University  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("import_researchers_upsert")

SOURCE_EXCEL_PATH = PROJECT_ROOT / "data" / "Researchers_Add_In.xlsx"

# Persian Excel header -> ORM/DB column name. The institution column is
# intentionally excluded here; it is resolved separately via the
# university name-to-id lookup (see resolve_university_id()).
COLUMN_MAPPING: dict[str, str] = {
    "کد ملی": "national_code",
    "کد رهگیری": "tracking_code",
    "نام نماینده": "first_name",
    "نام خانوادگی نماینده": "last_name",
    "تلفن همراه": "mobile",
    "ایمیل": "email",
    "درجه علمی": "academic_rank",
    "مدرک تحصیلی": "education_level",
    "نوع ثبت نام": "researcher_type",
    "وضعیت": "status",
}
UNIVERSITY_LOOKUP_COLUMN = "دانشگاه / محل خدمت"

NATIONAL_CODE_LENGTH = 10
DEFAULT_STATUS = "Active"

# Columns refreshed on conflict. ``is_deleted`` is appended separately below
# so a soft-deleted row is always restored, regardless of the source value.
UPDATABLE_COLUMNS = (
    "tracking_code",
    "first_name",
    "last_name",
    "full_name",
    "mobile",
    "email",
    "academic_rank",
    "education_level",
    "researcher_type",
    "status",
    "university_id",
)


class RowSkipped(Exception):
    """Raised internally when a row cannot be converted to a valid record.

    Attributes
    ----------
    reason : str
        One of ``"missing_university"`` or ``"invalid_data"``, used to
        route the row into the correct summary counter.
    """

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


def load_source_dataframe(excel_path: Path) -> pd.DataFrame:
    """Read the source workbook into a DataFrame.

    Args:
        excel_path: Absolute path to the researcher Excel workbook.

    Returns:
        The raw, unmodified worksheet contents.

    Raises:
        FileNotFoundError: If ``excel_path`` does not exist.
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Source Excel file not found: {excel_path}")

    dataframe = pd.read_excel(excel_path, engine="openpyxl")
    logger.info("Loaded %d rows from %s", len(dataframe), excel_path.name)
    return dataframe


def _clean_optional_text(value: Any) -> str | None:
    """Normalize an optional Excel cell to a stripped string or ``None``."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _strip_numeric_artifact(value: str) -> str:
    """Trim pandas' trailing ``.0`` float artifact from a numeric-looking ID."""
    if value.endswith(".0"):
        return value[:-2]
    return value


def _normalize_national_code(value: Any) -> str | None:
    """Normalize and zero-pad the primary-key column.

    Iranian national codes are 10 digits, but Excel frequently drops
    leading zeros when a numeric-looking ID column is stored as a number
    (and may also coerce it to a float, e.g. ``26746`` -> ``"26746.0"``).
    This strips the float artifact and left-pads with zeros to the
    standard 10-digit length.
    """
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    cleaned = _strip_numeric_artifact(cleaned)
    if not cleaned.isdigit():
        return cleaned  # Let the caller reject non-numeric codes explicitly.
    return cleaned.zfill(NATIONAL_CODE_LENGTH)


def build_university_lookup(session: Session) -> dict[str, str]:
    """Build a ``{stripped university name: national_id}`` lookup map.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A mapping from whitespace-stripped, active university name to its
        ``national_id``. When two active universities share a stripped
        name, the last one read wins and a warning is logged.
    """
    rows = (
        session.query(University.name, University.national_id)
        .filter(University.is_deleted == False)  # noqa: E712
        .all()
    )

    lookup: dict[str, str] = {}
    for name, national_id in rows:
        if name is None:
            continue
        key = name.strip()
        if key in lookup and lookup[key] != national_id:
            logger.warning(
                "Duplicate university name '%s' maps to multiple "
                "national_id values; using the last one seen.",
                key,
            )
        lookup[key] = national_id

    logger.info("Built university lookup with %d entries.", len(lookup))
    return lookup


def resolve_university_id(
    row: pd.Series,
    university_lookup: dict[str, str],
) -> str:
    """Resolve a row's free-text institution name to a ``university_id``.

    Args:
        row: A single row from the source DataFrame.
        university_lookup: Mapping built by :func:`build_university_lookup`.

    Returns:
        The matching university's ``national_id``.

    Raises:
        RowSkipped: If the institution name is blank or does not match any
            active university.
    """
    raw_name = _clean_optional_text(row.get(UNIVERSITY_LOOKUP_COLUMN))
    if raw_name is None:
        raise RowSkipped(
            "missing_university",
            f"Blank '{UNIVERSITY_LOOKUP_COLUMN}' value.",
        )

    university_id = university_lookup.get(raw_name.strip())
    if university_id is None:
        raise RowSkipped(
            "missing_university",
            f"Institution '{raw_name}' not found among active universities.",
        )
    return university_id


def row_to_researcher_record(
    row: pd.Series,
    university_lookup: dict[str, str],
) -> dict[str, Any]:
    """Convert one Excel row into a sanitized ``researchers`` row dict.

    Args:
        row: A single row from the source DataFrame.
        university_lookup: Mapping built by :func:`build_university_lookup`.

    Returns:
        A dict ready for the upsert statement.

    Raises:
        RowSkipped: If the row is missing a required field (national code,
            first name, last name) or its institution cannot be resolved.
    """
    national_code = _normalize_national_code(row.get("کد ملی"))
    if national_code is None or not national_code.isdigit():
        raise RowSkipped(
            "invalid_data", f"Missing or non-numeric national code: {national_code!r}."
        )
    if len(national_code) > NATIONAL_CODE_LENGTH:
        raise RowSkipped(
            "invalid_data",
            f"National code '{national_code}' exceeds "
            f"{NATIONAL_CODE_LENGTH} digits.",
        )

    first_name = _clean_optional_text(row.get("نام نماینده"))
    last_name = _clean_optional_text(row.get("نام خانوادگی نماینده"))
    if first_name is None or last_name is None:
        raise RowSkipped(
            "invalid_data",
            f"Missing first/last name for national code '{national_code}'.",
        )

    # Resolve the required university FK before doing anything else; this
    # is the only condition classified as "missing university" for the
    # summary, keeping it distinct from other invalid-data skips.
    university_id = resolve_university_id(row, university_lookup)

    tracking_code = _clean_optional_text(row.get("کد رهگیری"))
    if tracking_code is not None:
        tracking_code = _strip_numeric_artifact(tracking_code)

    record: dict[str, Any] = {
        "national_code": national_code,
        "tracking_code": tracking_code,
        "first_name": first_name,
        "last_name": last_name,
        "full_name": f"{first_name} {last_name}",
        "mobile": _mobile_as_text(row.get("تلفن همراه")),
        "email": _clean_optional_text(row.get("ایمیل")),
        "academic_rank": _clean_optional_text(row.get("درجه علمی")),
        "university_id": university_id,
        "education_level": _clean_optional_text(row.get("مدرک تحصیلی")),
        "researcher_type": _clean_optional_text(row.get("نوع ثبت نام")),
        "status": _clean_optional_text(row.get("وضعیت")) or DEFAULT_STATUS,
        "is_deleted": False,
    }
    return record


def _mobile_as_text(value: Any) -> str | None:
    """Clean a mobile-number cell, stripping any pandas float artifact."""
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    return _strip_numeric_artifact(cleaned)


def transform_dataframe(
    dataframe: pd.DataFrame,
    university_lookup: dict[str, str],
) -> tuple[list[dict[str, Any]], int, int]:
    """Convert every Excel row to sanitized upsert records.

    Duplicate ``national_code`` values within the source file are
    collapsed to the last occurrence, since PostgreSQL rejects an
    ``ON CONFLICT`` batch that targets the same conflict key twice.

    Args:
        dataframe: The raw source worksheet.
        university_lookup: Mapping built by :func:`build_university_lookup`.

    Returns:
        A tuple of (deduplicated records ready for upsert, rows skipped
        for a missing/unresolvable university, rows skipped for other
        invalid data).
    """
    records_by_national_code: dict[str, dict[str, Any]] = {}
    skipped_missing_university = 0
    skipped_invalid_data = 0

    for index, row in dataframe.iterrows():
        excel_row_number = index + 2  # 1-indexed plus header row offset.
        try:
            record = row_to_researcher_record(row, university_lookup)
        except RowSkipped as exc:
            if exc.reason == "missing_university":
                skipped_missing_university += 1
                logger.warning("Row %d skipped: %s", excel_row_number, exc)
            else:
                skipped_invalid_data += 1
                logger.warning("Row %d skipped: %s", excel_row_number, exc)
            continue

        records_by_national_code[record["national_code"]] = record

    return (
        list(records_by_national_code.values()),
        skipped_missing_university,
        skipped_invalid_data,
    )


def build_upsert_statement(records: list[dict[str, Any]]):
    """Build the native PostgreSQL ``INSERT ... ON CONFLICT DO UPDATE`` statement.

    All rows are batched into a single statement so the entire import
    commits atomically and PostgreSQL — not the application — resolves the
    insert-vs-update race for each ``national_code``.

    Args:
        records: Sanitized rows produced by :func:`transform_dataframe`.

    Returns:
        An executable SQLAlchemy ``Insert`` construct with the upsert
        clause attached.
    """
    insert_statement = pg_insert(Researcher).values(records)

    update_columns = {
        column: getattr(insert_statement.excluded, column)
        for column in UPDATABLE_COLUMNS
    }
    # Always restore a previously soft-deleted record on re-import.
    update_columns["is_deleted"] = False

    return insert_statement.on_conflict_do_update(
        index_elements=[Researcher.national_code],
        set_=update_columns,
    )


def run_upsert_import() -> None:
    """Execute the end-to-end upsert import and print a final summary."""
    try:
        dataframe = load_source_dataframe(SOURCE_EXCEL_PATH)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return

    session = SessionLocal()
    try:
        university_lookup = build_university_lookup(session)
    except SQLAlchemyError as exc:
        logger.error("Failed to load university lookup: %s", exc)
        session.close()
        return

    records, skipped_missing_university, skipped_invalid_data = transform_dataframe(
        dataframe, university_lookup
    )

    if not records:
        logger.warning("No valid rows to upsert; nothing was written.")
        session.close()
        return

    statement = build_upsert_statement(records)

    try:
        result = session.execute(statement)
        session.commit()
        processed_count = result.rowcount
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Upsert failed, transaction rolled back: %s", exc)
        return
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("RESEARCHER UPSERT SUMMARY")
    print("=" * 60)
    print(f"Source rows read:                 {len(dataframe)}")
    print(f"Skipped (missing/unmatched univ.): {skipped_missing_university}")
    print(f"Skipped (other invalid data):      {skipped_invalid_data}")
    print(f"Rows processed (upsert):           {processed_count}")
    print("=" * 60)


if __name__ == "__main__":
    run_upsert_import()


## File: scripts\import_universities.py
------------------------------
import pandas as pd
import sys
from pathlib import Path
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import engine, Base
from models.university import University


def import_universities():
    """Import universities from Excel file"""
    
    # Drop universities table with CASCADE to handle FK dependencies
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS universities CASCADE"))
    print("[OK] Dropped universities table with CASCADE")
    
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created/verified")
    
    # Read Excel file
    excel_path = "data/Universities.xlsx"
    print(f"Reading Excel from: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
        print(f"[OK] Loaded {len(df)} rows from Excel")
    except FileNotFoundError:
        print(f"[ERROR] Excel file not found at {excel_path}")
        return
    except Exception as e:
        print(f"[ERROR] Error reading Excel: {e}")
        return
    
    # Display column count (avoid printing Persian characters)
    print(f"Excel has {len(df.columns)} columns")
    
    # Column mapping (Persian headers to model fields)
    column_mapping = {
        'کد رهگیری': 'tracking_code',
        'شناسه ملی موسسه': 'national_id',
        'نام موسسه': 'name',
        'شهر': 'city',
        'آدرس': 'address',
        'استان موسسه': 'province',
        'نوع موسسه': 'university_type',
        'وضعیت': 'status'
    }
    
    # Start database session
    session = Session(bind=engine)
    
    try:
        # Performance optimization: Query existing national_ids once
        print("Fetching existing university records...")
        existing_ids = set(
            national_id for (national_id,) in session.query(University.national_id).all()
        )
        print(f"[OK] Found {len(existing_ids)} existing universities in database")
        
        # Counters
        added_count = 0
        skipped_count = 0
        error_count = 0
        
        print("\nProcessing records...")
        
        # Iterate through dataframe
        for index, row in df.iterrows():
            try:
                # Get national_id (primary key)
                national_id = row.get('شناسه ملی موسسه')
                
                # Convert pandas NaN to None and strip whitespaces
                national_id = None if pd.isna(national_id) else str(national_id).strip()
                
                # Skip if national_id is empty or already exists
                if not national_id:
                    skipped_count += 1
                    continue
                    
                if national_id in existing_ids:
                    skipped_count += 1
                    continue
                
                # Prepare university data
                university_data = {}
                for persian_col, field_name in column_mapping.items():
                    value = row.get(persian_col)
                    # Convert NaN to None, strip strings
                    if pd.isna(value):
                        university_data[field_name] = None
                    elif isinstance(value, str):
                        university_data[field_name] = value.strip()
                    else:
                        university_data[field_name] = value
                
                # Handle NOT NULL constraints - provide defaults for required fields
                # If university_type is None, set a default value
                if university_data.get('university_type') is None:
                    university_data['university_type'] = 'نامشخص'
                
                # If province is None, set a default value
                if university_data.get('province') is None:
                    university_data['province'] = 'نامشخص'
                
                # If name is None, skip this record
                if university_data.get('name') is None:
                    skipped_count += 1
                    continue
                
                # If status is None, set default
                if university_data.get('status') is None:
                    university_data['status'] = 'فعال'
                
                # Create University instance
                university = University(**university_data)
                session.add(university)
                
                # Add to existing_ids set to prevent duplicates in same batch
                existing_ids.add(national_id)
                added_count += 1
                
                # Commit in batches of 100
                if added_count % 100 == 0:
                    session.commit()
                    print(f"  Progress: {added_count} universities added, {skipped_count} skipped")
                
            except Exception as e:
                error_count += 1
                print(f"  Row {index + 1}: Error - {str(e)}")
                session.rollback()
                continue
        
        # Final commit
        session.commit()
        
        # Summary
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"[OK] Successfully imported: {added_count} universities")
        print(f"[SKIP] Skipped (duplicates/empty): {skipped_count}")
        print(f"[ERROR] Errors: {error_count}")
        print(f"Total rows processed: {len(df)}")
        print("="*60)
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Fatal error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    print("="*60)
    print("UNIVERSITY IMPORT SCRIPT")
    print("="*60)
    import_universities()


## File: scripts\import_universities_upsert.py
------------------------------
"""Idempotent upsert ETL for the ``universities`` table.

Loads university records from an Excel workbook and writes them to
PostgreSQL using a single native ``INSERT ... ON CONFLICT (national_id) DO
UPDATE`` statement (via ``sqlalchemy.dialects.postgresql.insert``). Unlike
``scripts/import_universities.py`` (the original truncate/reload loader),
this script never drops the table and never performs an application-level
"SELECT then INSERT/UPDATE" check — the conflict resolution happens
atomically inside PostgreSQL, which avoids the time-of-check to
time-of-use race that a Python-side existence check would introduce under
concurrent runs.

Soft-delete interaction: if a ``national_id`` re-appears in the source file
after having been soft-deleted (``is_deleted = True``), the update clause
forces ``is_deleted = False``, restoring the record instead of leaving it
hidden.

Usage
-----
    python scripts/import_universities_upsert.py
"""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# --- Windows console UTF-8 fix (Persian text in log/print output) ---------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running this script directly (adds project root to sys.path).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from models.university import University  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("import_universities_upsert")

SOURCE_EXCEL_PATH = PROJECT_ROOT / "data" / "Universities_Add_In.xlsx"

# Persian Excel header -> ORM/DB column name.
COLUMN_MAPPING: dict[str, str] = {
    "کد رهگیری": "tracking_code",
    "شناسه ملی موسسه": "national_id",
    "نام موسسه": "name",
    "نوع موسسه": "university_type",
    "استان": "province",
    "شهر": "city",
    "آدرس": "address",
    "وضعیت": "status",
}

# Safe defaults for NOT NULL columns that may be blank in the source file.
DEFAULT_PROVINCE = "نامشخص"
DEFAULT_UNIVERSITY_TYPE = "نامشخص"
DEFAULT_STATUS = "Active"

# Columns refreshed on conflict. ``is_deleted`` is appended separately below
# so a soft-deleted row is always restored, regardless of the source value.
UPDATABLE_COLUMNS = (
    "tracking_code",
    "name",
    "province",
    "university_type",
    "status",
    "city",
    "address",
)


def load_source_dataframe(excel_path: Path) -> pd.DataFrame:
    """Read the source workbook into a DataFrame.

    Args:
        excel_path: Absolute path to the university Excel workbook.

    Returns:
        The raw, unmodified worksheet contents.

    Raises:
        FileNotFoundError: If ``excel_path`` does not exist.
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Source Excel file not found: {excel_path}")

    dataframe = pd.read_excel(excel_path, engine="openpyxl")
    logger.info("Loaded %d rows from %s", len(dataframe), excel_path.name)
    return dataframe


def _clean_optional_text(value: Any) -> str | None:
    """Normalize an optional Excel cell to a stripped string or ``None``."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _normalize_national_id(value: Any) -> str | None:
    """Normalize the primary-key column, stripping pandas' float artifacts.

    Numeric ID columns read from Excel are frequently coerced to floats
    (e.g. ``10102894887`` becomes ``"10102894887.0"``); this trims a
    trailing ``.0`` so the value matches previously imported string IDs.
    """
    cleaned = _clean_optional_text(value)
    if cleaned is None:
        return None
    if cleaned.endswith(".0"):
        cleaned = cleaned[:-2]
    return cleaned


def row_to_university_record(row: pd.Series) -> dict[str, Any] | None:
    """Convert one Excel row into a sanitized ``universities`` row dict.

    Args:
        row: A single row from the source DataFrame.

    Returns:
        A dict ready for the upsert statement, or ``None`` if the row is
        missing a required identifier (``national_id`` or ``name``) and
        must be skipped.
    """
    national_id = _normalize_national_id(row.get("شناسه ملی موسسه"))
    name = _clean_optional_text(row.get("نام موسسه"))
    if national_id is None or name is None:
        return None

    record: dict[str, Any] = {
        "national_id": national_id,
        "name": name,
        "tracking_code": _clean_optional_text(row.get("کد رهگیری")),
        "city": _clean_optional_text(row.get("شهر")),
        "address": _clean_optional_text(row.get("آدرس")),
        "province": _clean_optional_text(row.get("استان")) or DEFAULT_PROVINCE,
        "university_type": (
            _clean_optional_text(row.get("نوع موسسه")) or DEFAULT_UNIVERSITY_TYPE
        ),
        "status": _clean_optional_text(row.get("وضعیت")) or DEFAULT_STATUS,
        "is_deleted": False,
    }
    return record


def transform_dataframe(dataframe: pd.DataFrame) -> tuple[list[dict[str, Any]], int]:
    """Convert every Excel row to sanitized upsert records.

    Duplicate ``national_id`` values within the source file are collapsed
    to the last occurrence, since PostgreSQL rejects an ``ON CONFLICT``
    batch that targets the same conflict key twice in one statement.

    Args:
        dataframe: The raw source worksheet.

    Returns:
        A tuple of (deduplicated records ready for upsert, skipped row
        count).
    """
    records_by_national_id: dict[str, dict[str, Any]] = {}
    skipped_count = 0

    for index, row in dataframe.iterrows():
        record = row_to_university_record(row)
        if record is None:
            skipped_count += 1
            logger.warning(
                "Row %d skipped: missing required national_id or name.",
                index + 2,  # +2: 1-indexed and header row offset.
            )
            continue
        records_by_national_id[record["national_id"]] = record

    return list(records_by_national_id.values()), skipped_count


def build_upsert_statement(records: list[dict[str, Any]]):
    """Build the native PostgreSQL ``INSERT ... ON CONFLICT DO UPDATE`` statement.

    All rows are batched into a single statement so the entire import
    commits atomically and PostgreSQL — not the application — resolves the
    insert-vs-update race for each ``national_id``.

    Args:
        records: Sanitized rows produced by :func:`transform_dataframe`.

    Returns:
        An executable SQLAlchemy ``Insert`` construct with the upsert
        clause attached.
    """
    insert_statement = pg_insert(University).values(records)

    update_columns = {
        column: getattr(insert_statement.excluded, column)
        for column in UPDATABLE_COLUMNS
    }
    # Always restore a previously soft-deleted record on re-import.
    update_columns["is_deleted"] = False

    return insert_statement.on_conflict_do_update(
        index_elements=[University.national_id],
        set_=update_columns,
    )


def run_upsert_import() -> None:
    """Execute the end-to-end upsert import and print a final summary."""
    try:
        dataframe = load_source_dataframe(SOURCE_EXCEL_PATH)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return

    records, skipped_count = transform_dataframe(dataframe)
    if not records:
        logger.warning("No valid rows to upsert; nothing was written.")
        return

    statement = build_upsert_statement(records)

    session = SessionLocal()
    try:
        result = session.execute(statement)
        session.commit()
        processed_count = result.rowcount
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Upsert failed, transaction rolled back: %s", exc)
        return
    finally:
        session.close()

    print("\n" + "=" * 60)
    print("UNIVERSITY UPSERT SUMMARY")
    print("=" * 60)
    print(f"Source rows read:         {len(dataframe)}")
    print(f"Rows skipped (invalid):   {skipped_count}")
    print(f"Rows processed (upsert):  {processed_count}")
    print("=" * 60)


if __name__ == "__main__":
    run_upsert_import()


## File: scripts\process_budgets.py
------------------------------
import re
import pandas as pd
from pathlib import Path

# ==========================================
# Configuration and Constants
# ==========================================
# Defining absolute paths using pathlib for Windows compatibility
BASE_DIR = Path(r"C:\Users\pchin\OneDrive\AI-Project\SATE_Fin_Dev\data")
INPUT_EXCEL_FILE = BASE_DIR / "Budget.xlsx"
OUTPUT_EXCEL_FILE = BASE_DIR / "Budget_longformat.xlsx"

ASSIGNED_SHEET_NAME = "Assigned_Budgets"
DEPOSIT_SHEET_NAME = "Deposit_Budget"
EMPLOYER_CODE_COL = "شماره طبقه بندی"

def clean_employer_code(value: str) -> str:
    """
    Normalizes the employer code by stripping whitespaces and removing trailing '.0'.
    Returns None if the value is invalid or empty.
    """
    if pd.isna(value):
        return None
    val_str = str(value).strip()
    if not val_str:
        return None
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def clean_financial_amount(value: str) -> float:
    """
    Cleans financial amount strings (removes commas, handles empty strings) 
    and converts them to float. Prevents calculation errors by returning 0.0 for blanks.
    """
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if not value:
            return 0.0
    return pd.to_numeric(value, errors="coerce")

def extract_fiscal_year(column_name: str) -> int:
    """
    Extracts the 4-digit fiscal year from a given column header.
    Raises ValueError if no year is found, preventing silent data corruption.
    """
    match = re.search(r"(\d{4})", str(column_name))
    if not match:
        raise ValueError(f"CRITICAL: Could not extract fiscal year from: {column_name}")
    return int(match.group(1))

def process_budget_data() -> None:
    """
    Main ETL pipeline: Reads multi-sheet Excel safely, melts data to long format,
    applies business logic, and exports to the exact target directory.
    """
    # 1. Validate Directory Existence
    if not BASE_DIR.exists():
        print(f"Error: The directory {BASE_DIR} does not exist.")
        return

    # 2. Read Excel File using ExcelFile for atomic loading and performance
    print(f"Loading data from: {INPUT_EXCEL_FILE}")
    try:
        with pd.ExcelFile(INPUT_EXCEL_FILE) as xls:
            df_assigned_wide = pd.read_excel(xls, sheet_name=ASSIGNED_SHEET_NAME)
            df_deposit_wide = pd.read_excel(xls, sheet_name=DEPOSIT_SHEET_NAME)
    except FileNotFoundError:
        print(f"Error: The file {INPUT_EXCEL_FILE} was not found.")
        return
    except ValueError as e:
        print(f"Error reading sheets: {e}")
        return

    # 3. Process Assigned Budgets (Mandates)
    print("Processing Assigned Budgets...")
    df_assigned_long = pd.melt(
        df_assigned_wide,
        id_vars=[EMPLOYER_CODE_COL],
        var_name="Year_Raw",
        value_name="Assigned_Amount"
    )
    df_assigned_long["Fiscal_Year"] = df_assigned_long["Year_Raw"].apply(extract_fiscal_year)
    df_assigned_long[EMPLOYER_CODE_COL] = df_assigned_long[EMPLOYER_CODE_COL].apply(clean_employer_code)
    #df_assigned_long["Assigned_Amount"] = df_assigned_long["Assigned_Amount"].apply(clean_financial_amount)
    df_assigned_long["Assigned_Amount"] = df_assigned_long["Assigned_Amount"].apply(clean_financial_amount) * 1_000_000_000
    
    # Implementing Soft Delete mechanism for database mapping
    df_assigned_long["Is_Deleted"] = False
    df_assigned_long.drop(columns=["Year_Raw"], inplace=True)

    # 4. Process Deposit Budgets
    print("Processing Deposit Budgets...")
    df_deposit_long = pd.melt(
        df_deposit_wide,
        id_vars=[EMPLOYER_CODE_COL],
        var_name="Year_Raw",
        value_name="Deposit_Amount"
    )
    df_deposit_long["Fiscal_Year"] = df_deposit_long["Year_Raw"].apply(extract_fiscal_year)
    df_deposit_long[EMPLOYER_CODE_COL] = df_deposit_long[EMPLOYER_CODE_COL].apply(clean_employer_code)
    df_deposit_long["Deposit_Amount"] = df_deposit_long["Deposit_Amount"].apply(clean_financial_amount)
    
    # Implementing Soft Delete mechanism
    df_deposit_long["Is_Deleted"] = False
    df_deposit_long.drop(columns=["Year_Raw"], inplace=True)

    # 5. Merge Data securely to prevent data loss (Outer Join)
    print("Merging data...")
    df_merged = pd.merge(
        df_assigned_long,
        df_deposit_long,
        on=[EMPLOYER_CODE_COL, "Fiscal_Year"],
        how="outer",
        suffixes=("_assigned", "_deposit")
    )
    
    # Resolving data nulls after outer merge to maintain mathematical accuracy
    df_merged["Is_Deleted"] = False 
    df_merged["Assigned_Amount"] = df_merged["Assigned_Amount"].fillna(0.0)
    df_merged["Deposit_Amount"] = df_merged["Deposit_Amount"].fillna(0.0)
    
    # Clean up: Remove rows where there is absolutely no financial activity
    df_merged = df_merged[(df_merged["Assigned_Amount"] > 0) | (df_merged["Deposit_Amount"] > 0)]

    # 6. Export to Excel in target directory
    print(f"Exporting processed data to: {OUTPUT_EXCEL_FILE}")
    with pd.ExcelWriter(OUTPUT_EXCEL_FILE, engine='xlsxwriter') as writer:
        df_merged.to_excel(writer, sheet_name='Merged_Master_Data', index=False)
        df_assigned_long.to_excel(writer, sheet_name='Assigned_LongFormat', index=False)
        df_deposit_long.to_excel(writer, sheet_name='Deposit_LongFormat', index=False)
    
    print("Data processing complete. Data integrity maintained.")

if __name__ == "__main__":
    process_budget_data()

## File: scripts\verify_universities.py
------------------------------
import sys
from pathlib import Path
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database import engine
from models.university import University

session = Session(bind=engine)

# Get total count
total = session.query(University).count()
print(f"Total universities in database: {total}")

# Get sample records
print("\nSample records:")
print("-" * 80)
for uni in session.query(University).limit(5):
    print(f"National ID: {uni.national_id}")
    print(f"Name: {uni.name}")
    print(f"Type: {uni.university_type}")
    print(f"Province: {uni.province}")
    print(f"Status: {uni.status}")
    print("-" * 80)

session.close()


## File: services\financial_engine.py
------------------------------
from decimal import Decimal
from typing import Sequence

import pandas as pd
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from models.contract import Contract
from models.deposits import AnnualMandate, DepositReceipt
from models.employer import Employer
from models.payment import Payment
from models.transfer import CreditTransfer


class InsufficientFundsError(ValueError):
    """Raised when a payment would exceed the employer's real balance.

    A ``ValueError`` subclass so existing ``except ValueError`` call sites
    still catch it, while callers that need to distinguish "insufficient
    funds" from other validation failures (e.g. "contract not found") can
    match on this specific type instead of parsing the error message.

    Attributes
    ----------
    employer_code : str
        The employer whose balance was insufficient.
    funding_year : int
        The funding year the balance was checked against.
    current_balance : float
        The employer's real balance before this payment.
    amount : float
        The payment amount that was rejected.
    deficit : float
        ``amount - current_balance`` — how much the payment exceeds the
        available balance, in Rials.
    """

    def __init__(
        self,
        employer_code: str,
        funding_year: int,
        current_balance: float,
        amount: float,
    ) -> None:
        self.employer_code = employer_code
        self.funding_year = funding_year
        self.current_balance = current_balance
        self.amount = amount
        self.deficit = amount - current_balance
        super().__init__(
            "موجودی کافی نیست: "
            f"مانده فعلی کارفرما '{employer_code}' برای سال مالی "
            f"{funding_year} برابر {current_balance:,.0f} ریال است، اما "
            f"مبلغ درخواستی {amount:,.0f} ریال می‌باشد "
            f"(کسری: {self.deficit:,.0f} ریال)."
        )


def lock_active_contracts(
    db: Session,
    contract_codes: Sequence[str],
) -> dict[str, Contract]:
    """
    Lock and return active contracts in deterministic tracking-code order.

    PostgreSQL keeps the row-level locks until the surrounding transaction
    commits or rolls back. Sorting the unique keys gives concurrent payment
    transactions a consistent lock order and reduces deadlock risk.

    Args:
        db: Active SQLAlchemy session with an open transaction.
        contract_codes: Contract tracking codes that participate in the
            financial operation.

    Returns:
        A mapping from tracking code to the locked active contract.
    """
    unique_codes = sorted(set(contract_codes))
    if not unique_codes:
        return {}

    contracts = (
        db.query(Contract)
        .filter(
            Contract.tracking_code.in_(unique_codes),
            Contract.is_deleted == False,
        )
        .order_by(Contract.tracking_code)
        .with_for_update()
        .all()
    )
    return {contract.tracking_code: contract for contract in contracts}


def lock_active_employers(
    db: Session,
    employer_codes: Sequence[str],
) -> dict[str, Employer]:
    """
    Lock and return active employers in deterministic classification-code order.

    The employer row is the serialization point for balance-changing operations.
    Callers must retain the same transaction while calculating balances and
    inserting payments so concurrent requests cannot validate stale balances.

    Args:
        db: Active SQLAlchemy session with an open transaction.
        employer_codes: Employer classification codes to serialize.

    Returns:
        A mapping from classification code to the locked active employer.
    """
    unique_codes = sorted(set(employer_codes))
    if not unique_codes:
        return {}

    employers = (
        db.query(Employer)
        .filter(
            Employer.classification_code.in_(unique_codes),
            Employer.is_deleted == False,
        )
        .order_by(Employer.classification_code)
        .with_for_update()
        .all()
    )
    return {employer.classification_code: employer for employer in employers}


def lock_active_contract_and_employer(
    db: Session,
    contract_code: str,
) -> tuple[Contract, Employer]:
    """
    Lock one active contract and its active employer for financial processing.

    Args:
        db: Active SQLAlchemy session with an open transaction.
        contract_code: Tracking code of the contract to lock.

    Returns:
        The locked contract and its locked employer.

    Raises:
        ValueError: If the contract or linked employer is missing or soft-deleted.
    """
    contract = lock_active_contracts(db, [contract_code]).get(contract_code)
    if contract is None:
        raise ValueError(
            f"Contract with tracking code '{contract_code}' not found or has been deleted."
        )

    employer = lock_active_employers(db, [contract.employer_code]).get(
        contract.employer_code
    )
    if employer is None:
        raise ValueError(
            f"Employer with classification code '{contract.employer_code}' "
            "not found or has been deleted."
        )

    return contract, employer


def get_contracts_with_dynamic_status(
    db: Session,
    threshold_year: int = 1402,
):
    """
    Retrieve contracts with a lifecycle status calculated entirely in SQL.

    Non-deleted payments are aggregated per non-deleted contract. A contract is
    completed when its total payments cover its total amount. Otherwise, its
    most recent activity year is the greater of the last payment funding year
    and the approximated Jalali contract creation year. Activity before
    ``threshold_year`` is classified as stagnant; all other activity is active.
    The persisted ``Contract.status`` column is never modified.

    Args:
        db: Active SQLAlchemy database session.
        threshold_year: Jalali year used as the active/stagnant boundary.

    Returns:
        SQLAlchemy result rows containing the contract entity, aggregated
        payment values, Jalali activity years, and the dynamic status.
    """
    total_paid = func.coalesce(func.sum(Payment.amount), 0)
    last_payment_funding_year = func.max(Payment.funding_year)
    gregorian_contract_year = func.extract("year", Contract.contract_date)
    contract_creation_year = case(
        (
            func.to_char(Contract.contract_date, "MMDD") < "0321",
            gregorian_contract_year - 622,
        ),
        else_=gregorian_contract_year - 621,
    )
    activity_year = func.greatest(
        func.coalesce(last_payment_funding_year, contract_creation_year, 0),
        func.coalesce(contract_creation_year, last_payment_funding_year, 0),
    )
    dynamic_status = case(
        (total_paid >= Contract.total_amount, "Completed"),
        (activity_year < threshold_year, "Stagnant"),
        else_="Active",
    )

    statement = (
        select(
            Contract,
            total_paid.label("total_paid"),
            func.coalesce(last_payment_funding_year, 0).label(
                "last_payment_funding_year"
            ),
            contract_creation_year.label("contract_creation_year"),
            activity_year.label("activity_year"),
            dynamic_status.label("dynamic_status"),
        )
        .outerjoin(
            Payment,
            and_(
                Payment.contract_tracking_code == Contract.tracking_code,
                Payment.is_deleted == False,
            ),
        )
        .where(Contract.is_deleted == False)
        .group_by(Contract.tracking_code)
    )

    return db.execute(statement).all()


def calculate_real_balance(
    db: Session,
    employer_code: str,
    funding_year: int,
    *,
    lock_employer: bool = False,
) -> float:
    """
    Calculate the real balance for an active employer and funding year.

    Formula: ``(Deposits + Transfers In) - (Payments + Transfers Out)``.
    "Payments" includes both ``Final`` and ``Draft`` status rows: a draft
    reserves funds against the employer's balance the moment it is staged
    in the batch-payment cart, so a second draft cannot be added against
    money a first, not-yet-finalized draft has already claimed.

    Args:
        db: Active SQLAlchemy database session.
        employer_code: Employer classification code.
        funding_year: Funding year used by all balance components.
        lock_employer: When true, acquire a PostgreSQL ``FOR UPDATE`` lock on
            the active employer row before reading financial aggregates. The
            caller must keep the transaction open through the related write.

    Returns:
        The calculated balance in base Rials.

    Raises:
        ValueError: If ``lock_employer`` is true and the employer is missing or
            soft-deleted.
    """
    if lock_employer and employer_code not in lock_active_employers(
        db, [employer_code]
    ):
        raise ValueError(
            f"Employer with classification code '{employer_code}' "
            "not found or has been deleted."
        )

    deposits_query = db.query(func.sum(DepositReceipt.deposit_amount)).join(
        Employer, DepositReceipt.employer_code == Employer.classification_code
    ).filter(
        or_(
            Employer.classification_code == employer_code,
            Employer.parent_code == employer_code,
        ),
        DepositReceipt.fiscal_year == funding_year,
        DepositReceipt.is_deleted == False,
        Employer.is_deleted == False,
    ).scalar()
    total_deposits = deposits_query or Decimal("0.0")

    payments_query = db.query(func.sum(Payment.amount)).join(
        Contract, Payment.contract_tracking_code == Contract.tracking_code
    ).filter(
        Contract.employer_code == employer_code,
        Payment.funding_year == funding_year,
        Payment.is_deleted == False,
        Payment.status.in_(("Final", "Draft")),
        Contract.is_deleted == False,
    ).scalar()
    total_payments = payments_query or Decimal("0.0")

    transfers_out_query = db.query(func.sum(CreditTransfer.amount)).join(
        Employer, CreditTransfer.source_employer_code == Employer.classification_code
    ).filter(
        or_(
            Employer.classification_code == employer_code,
            Employer.parent_code == employer_code,
        ),
        CreditTransfer.fiscal_year == funding_year,
        CreditTransfer.is_deleted == False,
        Employer.is_deleted == False,
    ).scalar()
    transfers_out = transfers_out_query or Decimal("0.0")

    transfers_in_query = db.query(func.sum(CreditTransfer.amount)).filter(
        CreditTransfer.destination_employer_code == employer_code,
        CreditTransfer.fiscal_year == funding_year,
        CreditTransfer.is_deleted == False,
    ).scalar()
    transfers_in = transfers_in_query or Decimal("0.0")

    real_balance = total_deposits + transfers_in - transfers_out - total_payments
    return float(real_balance)


def get_mandated_amount(db: Session, employer_code: str, fiscal_year: int) -> float:
    """
    Retrieves the mandated budget amount (اعتبار تکلیفی) for a specific employer.
    """
    mandate = db.query(AnnualMandate).filter(
        AnnualMandate.employer_code == employer_code,
        AnnualMandate.fiscal_year == fiscal_year,
        AnnualMandate.is_deleted == False
    ).first()
    
    return float(mandate.mandated_amount) if mandate else 0.0


def _codes_to_include(db: Session, employer: Employer) -> list[str]:
    """Return employer code plus subsidiary codes for Mother entities."""
    if employer.employer_type == "Mother":
        subsidiaries = db.query(Employer.classification_code).filter(
            Employer.parent_code == employer.classification_code,
            Employer.is_deleted == False,
        ).all()
        return [employer.classification_code] + [s[0] for s in subsidiaries]
    return [employer.classification_code]


def get_all_employers_financials(db: Session) -> pd.DataFrame:
    """
    Aggregate financial data for all active employers across all fiscal years.

    For Mother employers, deposits, mandates, payments, and transfers are rolled up
    to include all subsidiaries. Balance formula (single source of truth):

        (Total Deposits + Transfers In) - (Total Payments + Transfers Out)
    """
    employers = db.query(Employer).filter(
        Employer.status == "Active",
        Employer.is_deleted == False,
    ).all()

    all_data = []

    for employer in employers:
        employer_code = employer.classification_code
        employer_name = employer.name
        codes_to_include = _codes_to_include(db, employer)

        mandates_query = db.query(
            AnnualMandate.fiscal_year.label("year"),
            func.sum(AnnualMandate.mandated_amount).label("mandated_amount"),
        ).filter(
            AnnualMandate.employer_code.in_(codes_to_include),
            AnnualMandate.is_deleted == False,
        ).group_by(AnnualMandate.fiscal_year)

        deposits_query = db.query(
            DepositReceipt.fiscal_year.label("year"),
            func.sum(DepositReceipt.deposit_amount).label("deposit_amount"),
        ).filter(
            DepositReceipt.employer_code.in_(codes_to_include),
            DepositReceipt.is_deleted == False,
        ).group_by(DepositReceipt.fiscal_year)

        payments_query = db.query(
            Payment.funding_year.label("year"),
            func.sum(Payment.amount).label("payment_amount"),
        ).join(
            Contract, Payment.contract_tracking_code == Contract.tracking_code
        ).filter(
            Contract.employer_code.in_(codes_to_include),
            Payment.is_deleted == False,
            Contract.is_deleted == False,
        ).group_by(Payment.funding_year)

        transfers_in_query = db.query(
            CreditTransfer.fiscal_year.label("year"),
            func.sum(CreditTransfer.amount).label("transfer_in"),
        ).filter(
            CreditTransfer.destination_employer_code.in_(codes_to_include),
            CreditTransfer.is_deleted == False,
        ).group_by(CreditTransfer.fiscal_year)

        transfers_out_query = db.query(
            CreditTransfer.fiscal_year.label("year"),
            func.sum(CreditTransfer.amount).label("transfer_out"),
        ).filter(
            CreditTransfer.source_employer_code.in_(codes_to_include),
            CreditTransfer.is_deleted == False,
        ).group_by(CreditTransfer.fiscal_year)

        metric_frames = []
        for query, columns in (
            (mandates_query, ["year", "mandated_amount"]),
            (deposits_query, ["year", "deposit_amount"]),
            (payments_query, ["year", "payment_amount"]),
            (transfers_in_query, ["year", "transfer_in"]),
            (transfers_out_query, ["year", "transfer_out"]),
        ):
            df_metric = pd.read_sql(query.statement, db.bind)
            df_metric = df_metric.reindex(columns=columns).fillna(0.0)
            metric_frames.append(df_metric)

        df_merged = metric_frames[0]
        for df_metric in metric_frames[1:]:
            df_merged = df_merged.merge(df_metric, on="year", how="outer")

        df_merged = df_merged.fillna(0).infer_objects(copy=False)
        df_merged["employer_code"] = employer_code
        df_merged["employer_name"] = employer_name

        required_cols = [
            "mandated_amount",
            "deposit_amount",
            "payment_amount",
            "transfer_in",
            "transfer_out",
        ]
        for col in required_cols:
            if col not in df_merged.columns:
                df_merged[col] = 0.0

        df_merged["balance"] = (
            df_merged["deposit_amount"] + df_merged["transfer_in"]
        ) - (
            df_merged["payment_amount"] + df_merged["transfer_out"]
        )

        all_data.append(df_merged)

    if not all_data:
        return pd.DataFrame()

    df_all = pd.concat(all_data, ignore_index=True)
    return df_all[
        [
            "employer_code",
            "employer_name",
            "year",
            "mandated_amount",
            "deposit_amount",
            "payment_amount",
            "transfer_in",
            "transfer_out",
            "balance",
        ]
    ]


def validate_payment_impact(
    db: Session,
    contract_code: str,
    payment_amount: float,
    funding_year: int,
    *,
    lock_rows: bool = False,
) -> dict:
    """
    Validate a payment's impact on the linked employer's real balance.

    Supersedes the original FR-18/FR-19/FR-20 "warn but allow" behavior:
    negative balances are now a **hard block**, not a warning. A projected
    balance below zero raises :class:`InsufficientFundsError` instead of
    being reported through an ``is_negative`` flag — there is no longer a
    success return path for an unaffordable payment.

    Args:
        db: Active SQLAlchemy database session.
        contract_code: Contract tracking code linked to the payment.
        payment_amount: Payment amount in base Rials.
        funding_year: Funding year for the payment.
        lock_rows: When true, lock the active contract and employer rows for
            the duration of the caller's transaction.

    Returns:
        A dictionary containing employer code, current balance, payment
        amount, and projected balance — always affordable, since an
        unaffordable payment raises instead of returning.

    Raises:
        ValueError: If the contract or linked employer is missing or
            soft-deleted.
        InsufficientFundsError: If ``current_balance - payment_amount`` is
            negative.
    """
    if lock_rows:
        contract, _ = lock_active_contract_and_employer(db, contract_code)
    else:
        contract = (
            db.query(Contract)
            .join(
                Employer,
                and_(
                    Contract.employer_code == Employer.classification_code,
                    Employer.is_deleted == False,
                ),
            )
            .filter(
                Contract.tracking_code == contract_code,
                Contract.is_deleted == False,
            )
            .first()
        )

    if contract is None:
        raise ValueError(
            f"Contract with tracking code '{contract_code}' not found or has been deleted."
        )

    employer_code = contract.employer_code
    current_balance = calculate_real_balance(db, employer_code, funding_year)
    new_balance = current_balance - payment_amount

    if new_balance < 0:
        raise InsufficientFundsError(
            employer_code, funding_year, current_balance, payment_amount
        )

    return {
        "employer_code": employer_code,
        "current_balance": current_balance,
        "payment_amount": payment_amount,
        "new_balance": new_balance,
        "is_negative": False,
    }


