# Directory Structure
./
    create_project_structure.py
    generate_context.py
    main.py
    SATE_codebase_context.md
    test_engine_cli.py
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
    dashboard/
        app.py
        app_v2.py
        CHANGELOG.md
        QUICKSTART.md
        README.md
        views/
            batch_payments_page.py
            contract_entry_page.py
            researcher_entry_page.py
            university_entry_page.py
    data/
        Archive/
            Payments/
    Docs/
        Phase1_Complete.md
        Phase2_Start.md
        Phase3_Dashboard_Complete.md
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
        append_new_mandates.py
        chart01_total_trend.py
        check_excel.py
        create_transfer_table.py
        example_1.py
        generate_contract_status_report.py
        generate_financial_report.py
        import_contracts.py
        import_credit_transfers.py
        import_deposits.py
        import_employers.py
        import_payments.py
        import_researchers.py
        import_universities.py
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
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.database import get_db
from models.contract import Contract
from models.employer import Employer
from models.researchers import Researcher
from models.university import University
from schemas.contract_schema import ContractCreate, ContractSearchResult

router = APIRouter(prefix="/contracts", tags=["Contracts"])

DUPLICATE_CONTRACT_MESSAGE = (
    "قراردادی با کد رهگیری '{tracking_code}' قبلاً ثبت شده است. "
    "لطفاً از ارسال مجدد فرم خودداری کنید."
)


def _optional_text(value: str | None) -> str | None:
    """Normalize optional text values before database persistence."""
    if value is None:
        return None
    normalized_value = value.strip()
    return normalized_value or None


def _get_active_contract_parties(
    db: Session,
    payload: ContractCreate,
) -> tuple[Employer, University, Researcher]:
    """Load active contract parties and enforce employer business rules."""
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
    if employer.employer_type == "Subsidiary":
        raise HTTPException(
            status_code=400,
            detail=(
                "خطا: شرکت‌های زیرمجموعه مجاز به انعقاد قرارداد نمی‌باشند. "
                "قرارداد باید به نام شرکت مادر ثبت شود."
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
    """Register a contract and gracefully reject duplicate submissions."""
    tracking_code = payload.tracking_code.strip()
    title = payload.title.strip()
    if not tracking_code or not title:
        raise HTTPException(
            status_code=400,
            detail="کد رهگیری و عنوان قرارداد الزامی هستند.",
        )

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

    employer, university, researcher = _get_active_contract_parties(db, payload)
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
        contract_date=payload.contract_date,
        duration_months=payload.duration_months,
        status="فعال",
        is_deleted=False,
    )
    db.add(contract)

    try:
        db.commit()
        db.refresh(contract)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=DUPLICATE_CONTRACT_MESSAGE.format(
                tracking_code=tracking_code
            ),
        ) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="خطا در ذخیره قرارداد. لطفاً مجدداً تلاش کنید.",
        ) from exc

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
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from models.payment import Payment
from schemas.payment_schema import (
    PaymentBatchValidationRequest,
    PaymentBatchValidationResponse,
    PaymentBulkCreate,
    PaymentBulkCreateResponse,
    PaymentValidationRequest,
    PaymentValidationResponse,
)
from services.financial_engine import (
    calculate_real_balance,
    lock_active_contract_and_employer,
    lock_active_contracts,
    lock_active_employers,
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
    Validate the impact of a payment on the employer's balance before registration.
    
    This endpoint implements FR-18, FR-19, FR-20:
    - Finds the employer linked to the contract
    - Calculates current and projected balance
    - Warns if balance becomes negative (but does not block the operation)
    
    **Business Rule:** This endpoint returns HTTP 200 even if the balance becomes negative,
    as the system is designed to warn but not prevent negative balances.
    
    **Parameters:**
    - `contract_tracking_code`: The contract tracking code
    - `amount`: The payment amount to validate
    - `funding_year`: The funding year for the payment
    
    **Returns:**
    - Current balance, new balance, and warning message if applicable
    """
    
    try:
        # Call the financial engine to validate payment impact
        validation_result = validate_payment_impact(
            db=db,
            contract_code=request.contract_tracking_code,
            payment_amount=request.amount,
            funding_year=request.funding_year,
            lock_rows=True,
        )
        
        # Prepare warning message if balance becomes negative
        warning_message = None
        if validation_result["is_negative"]:
            warning_message = "هشدار: ثبت این پرداخت باعث منفی شدن مانده حساب کارفرما خواهد شد"
        
        # Build and return response
        return PaymentValidationResponse(
            employer_code=validation_result["employer_code"],
            current_balance=validation_result["current_balance"],
            payment_amount=validation_result["payment_amount"],
            new_balance=validation_result["new_balance"],
            is_negative=validation_result["is_negative"],
            warning_message=warning_message
        )
        
    except ValueError as e:
        # Contract not found or deleted
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected error during validation
        raise HTTPException(
            status_code=500,
            detail=f"Error validating payment: {str(e)}"
        )


@router.post("/validate-draft", response_model=PaymentBatchValidationResponse)
def validate_draft_payment(
    request: PaymentBatchValidationRequest,
    db: Session = Depends(get_db),
):
    """
    Validate a single drafted (cart) payment against the employer's balance.

    The available balance is computed as the current database balance minus the
    `pending_cart_amount` (other drafts already reserved in the frontend cart
    for the same employer). If the payment amount exceeds the available balance,
    the request is rejected with HTTP 400 and the exact remaining balance.

    **Parameters:**
    - `contract_tracking_code`: Contract linked to the drafted payment.
    - `amount`: Amount of the drafted payment.
    - `funding_year`: Funding (budget consumption) year.
    - `pending_cart_amount`: Sum of other drafts for the same employer in the cart.

    **Returns:**
    - HTTP 200 with balance breakdown when the draft is affordable.
    - HTTP 400 with the remaining balance when funds are insufficient.
    """
    try:
        contract, _ = lock_active_contract_and_employer(
            db, request.contract_tracking_code
        )
        current_db_balance = calculate_real_balance(
            db, contract.employer_code, request.funding_year
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating balance: {str(exc)}",
        )

    available_balance = current_db_balance - request.pending_cart_amount

    if available_balance < request.amount:
        raise HTTPException(
            status_code=400,
            detail=(
                "Insufficient funds for this draft payment. "
                f"Remaining available balance is {available_balance:,.0f} Rials, "
                f"but the requested amount is {request.amount:,.0f} Rials."
            ),
        )

    return PaymentBatchValidationResponse(
        employer_code=contract.employer_code,
        current_db_balance=current_db_balance,
        pending_cart_amount=request.pending_cart_amount,
        available_balance=available_balance,
        amount=request.amount,
        remaining_balance=available_balance - request.amount,
        is_valid=True,
    )


@router.post("/bulk-submit", response_model=PaymentBulkCreateResponse, status_code=201)
def bulk_submit_payments(
    request: PaymentBulkCreate,
    db: Session = Depends(get_db),
):
    """
    Register a payment batch in one pessimistically locked transaction.

    Active contract and employer rows are locked with PostgreSQL ``FOR UPDATE``
    before balances are calculated. Locks are acquired in deterministic order
    and held through all inserts and the commit. Negative balances do not block
    or roll back registration; they are returned as FR-20 warning messages.

    Args:
        request: Validated batch of payments to register atomically.
        db: Active SQLAlchemy database session.

    Returns:
        The committed tracking codes and any negative-balance warnings.

    Raises:
        HTTPException: If identifiers are duplicated, missing, or soft-deleted,
            or if the database transaction fails.
    """
    tracking_codes = [item.tracking_code for item in request.payments]
    seen_codes: set[str] = set()
    duplicate_request_code = None
    for tracking_code in tracking_codes:
        if tracking_code in seen_codes:
            duplicate_request_code = tracking_code
            break
        seen_codes.add(tracking_code)

    if duplicate_request_code is not None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"خطا: کد رهگیری پرداخت '{duplicate_request_code}' "
                "قبلاً در سیستم ثبت شده است."
            ),
        )

    running_balances: dict[tuple[str, int], float] = {}
    created_tracking_codes: List[str] = []
    warning_messages: List[str] = []

    try:
        existing = (
            db.query(Payment.tracking_code)
            .filter(
                Payment.tracking_code.in_(tracking_codes),
                Payment.is_deleted == False,
            )
            .first()
        )
        if existing:
            duplicate_code = existing[0]
            raise HTTPException(
                status_code=400,
                detail=(
                    f"خطا: کد رهگیری پرداخت '{duplicate_code}' "
                    "قبلاً در سیستم ثبت شده است."
                ),
            )

        contract_codes = [
            item.contract_tracking_code for item in request.payments
        ]
        locked_contracts = lock_active_contracts(db, contract_codes)
        missing_contract_codes = sorted(
            set(contract_codes) - set(locked_contracts)
        )
        if missing_contract_codes:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Contract '{missing_contract_codes[0]}' not found or "
                    "has been deleted."
                ),
            )

        employer_codes = [
            contract.employer_code for contract in locked_contracts.values()
        ]
        locked_employers = lock_active_employers(db, employer_codes)
        missing_employer_codes = sorted(
            set(employer_codes) - set(locked_employers)
        )
        if missing_employer_codes:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Employer '{missing_employer_codes[0]}' not found or "
                    "has been deleted."
                ),
            )

        for index, item in enumerate(request.payments):
            contract = locked_contracts[item.contract_tracking_code]
            balance_key = (contract.employer_code, item.funding_year)
            if balance_key not in running_balances:
                running_balances[balance_key] = calculate_real_balance(
                    db, contract.employer_code, item.funding_year
                )

            payment = Payment(
                tracking_code=item.tracking_code,
                contract_tracking_code=item.contract_tracking_code,
                series=item.series,
                amount=item.amount,
                notification_letter_number=item.notification_letter_number,
                notification_date=item.notification_date,
                payment_year=item.payment_year,
                funding_year=item.funding_year,
                attachment_path=item.attachment_path,
                is_deleted=False,
            )
            db.add(payment)

            running_balances[balance_key] -= item.amount
            if running_balances[balance_key] < 0:
                warning_messages.append(
                    f"Row {index + 1} (tracking code '{item.tracking_code}'): "
                    f"employer '{contract.employer_code}' balance for funding "
                    f"year {item.funding_year} is negative "
                    f"({running_balances[balance_key]:,.0f} Rials) after registration."
                )
            created_tracking_codes.append(item.tracking_code)

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error during bulk submission (transaction rolled back): {str(exc)}",
        )

    return PaymentBulkCreateResponse(
        message=(
            "All payments were registered successfully with balance warnings."
            if warning_messages
            else "All payments were registered successfully."
        ),
        submitted_count=len(created_tracking_codes),
        tracking_codes=created_tracking_codes,
        warning_messages=warning_messages,
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
import os
from sqlalchemy import create_engine
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

def get_db():
    """Dependency to yield database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    university_entry_page = st.Page("views/university_entry_page.py", title="ثبت موسسه مجری", icon="🏫")
    researcher_entry_page = st.Page("views/researcher_entry_page.py", title="ثبت اطلاعات فناور", icon="🧑‍🔬")

    # 3. Group and initialize navigation.
    pg = st.navigation({
        "داشبوردهای مدیریتی": [dash_page],
        "فرم‌های ورود اطلاعات": [batch_payments_page, contract_entry_page, university_entry_page, researcher_entry_page],
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
# File: pages/batch_payments_page.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Backend API Base URL
API_URL = "http://127.0.0.1:8000/api/v1"

# ─── Aggressive RTL override + compact Persian theme ───
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
/* Compact headers and rules so all sections fit without excessive scrolling */
h1 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; padding: 0 !important; }
h2, h3 { margin-top: 0.15rem !important; margin-bottom: 0.15rem !important; padding: 0 !important; }
hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
.stBlock, .stVerticalBlock, [data-testid="stVerticalBlock"] > div {
    margin-top: 0.1rem !important;
    margin-bottom: 0.1rem !important;
}
</style>
""", unsafe_allow_html=True)


st.title("📂 فرم ثبت دسته‌ای لیست پرداخت (کارتابل صندوق عتف)")

# 1. Initialize Temporary Cart in Session State
if "payment_cart" not in st.session_state:
    st.session_state.payment_cart = []

# 2. Top Bar: Global Batch Configuration
st.subheader("۱. اطلاعات کلی لیست پرداخت")
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    series_number = st.number_input("شماره سری پرداخت (لیست):", min_value=1, value=15, step=1)
with col_s2:
    # Default to current Jalali year (1405 based on conceptual doc context)
    payment_year = st.number_input("سال پرداخت (شمسی):", min_value=1398, max_value=1410, value=1405)
with col_s3:
    st.info("💡 این اطلاعات به طور خودکار به تمام ردیف‌های این لیست اعمال خواهد شد.")

st.markdown("---")

# 3. Data Entry Section (Row by Row)
st.subheader("۲. ورود اطلاعات ردیف جدید")

# Live search for contracts
search_query = st.text_input("🔍 جستجوی قرارداد (کد رهگیری یا بخشی از عنوان قرارداد):")
selected_contract = None

if search_query:
    try:
        response = requests.get(f"{API_URL}/contracts/search", params={"q": search_query}, timeout=5)
        if response.status_code == 200 and response.json():
            contracts_found = response.json()
            # Format display for the selectbox
            options = {f"{c['contract_tracking_code']} - {c['title'][:40]}...": c for c in contracts_found}
            choice = st.selectbox("قرارداد مورد نظر را انتخاب کنید:", list(options.keys()))
            selected_contract = options[choice]
            
            # Auto-fill Read-only data to assure the clerk
            st.success(f"🏢 متقاضی (شرکت مادر): {selected_contract['employer_name']} | 🎓 مجری: {selected_contract['university_name']} | 🧑‍💻 فناور: {selected_contract['researcher_name']}")
        else:
            st.warning("هیچ قراردادی با این مشخصات یافت نشد.")
    except requests.exceptions.ConnectionError:
        st.error("خطا: امکان اتصال به سرور بک‌اند وجود ندارد. لطفاً مطمئن شوید سرور اصلی (FastAPI) روی پورت 8000 در حال اجرا است.")
    except requests.exceptions.Timeout:
        st.error("خطا: پاسخ از سرور بک‌اند بیش از حد طول کشید. لطفاً مجدداً تلاش کنید.")
    except Exception as e:
        st.error(f"خطا در اتصال به بک‌اند: {e}")

# Other input fields for the row
col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    pay_tracking_code = st.text_input("کد رهگیری پرداخت (از سامانه ساتع):")
with col_r2:
    amount = st.number_input("مبلغ پرداختی (ریال):", min_value=0.0, step=1000000.0, format="%.2f")
with col_r3:
    funding_year = st.number_input("پرداخت از محل سال مالی (شمسی):", min_value=1398, max_value=1410, value=1402)

# Row Validation and Insertion into Temporary Cart
if st.button("➕ بررسی و اضافه کردن به لیست"):
    if not selected_contract or not pay_tracking_code or amount <= 0:
        st.error("لطفاً تمامی فیلدهای الزامی ردیف را تکمیل کنید.")
    else:
        # Calculate pending amount for this employer in the current cart
        employer_code = selected_contract['employer_classification_code']
        pending_amount = sum(item['amount'] for item in st.session_state.payment_cart 
                             if item['employer_code'] == employer_code and item['funding_year'] == funding_year)
        
        # Call Backend to validate draft with pending cart consideration
        val_payload = {
            "contract_tracking_code": selected_contract['contract_tracking_code'],
            "amount": amount,
            "funding_year": funding_year,
            "pending_cart_amount": pending_amount
        }
        
        try:
            val_response = requests.post(f"{API_URL}/payments/validate-draft", json=val_payload)
            if val_response.status_code == 200:
                # Add to local state (Memory Cart)
                new_row = {
                    "tracking_code": pay_tracking_code,
                    "contract_tracking_code": selected_contract['contract_tracking_code'],
                    "title": selected_contract['title'],
                    "employer_name": selected_contract['employer_name'],
                    "employer_code": employer_code,
                    "amount": amount,
                    "funding_year": funding_year,
                    "payment_year": payment_year,
                    "series": str(series_number)
                }
                st.session_state.payment_cart.append(new_row)
                st.toast("✅ ردیف با موفقیت تایید و به لیست پیش‌نویس اضافه شد.", icon="🔥")
            else:
                err_detail = val_response.json().get('detail', 'موجودی کافی نیست.')
                st.error(f"❌ خطای عدم کفایت موجودی: {err_detail}")
        except Exception as e:
            st.error(f"خطا در ارتباط با سرور اعتبارسنجی: {e}")

st.markdown("---")

# 4. Display Current Temporary Cart Table
st.subheader("۳. لیست پیش‌نویس پرداخت‌های در حال انتظار (ثبت موقت)")
if st.session_state.payment_cart:
    df_cart = pd.DataFrame(st.session_state.payment_cart)
    # Re-order columns for display
    display_df = df_cart[['series', 'tracking_code', 'contract_tracking_code', 'employer_name', 'amount', 'funding_year', 'payment_year']]
    display_df.columns = ['سری', 'کد رهگیری پرداخت', 'کد قرارداد', 'نام کارفرما', 'مبلغ (ریال)', 'محل سال مالی', 'سال خروج پول']
    st.dataframe(display_df, width="stretch")
    
    if st.button("🗑️ خالی کردن کل لیست"):
        st.session_state.payment_cart = []
        st.rerun()
        
    st.markdown("### 🚀 نهایی‌سازی و ثبت در دیتابیس")
    if st.button("💾 تأیید نهایی و ارسال لیست به صندوق", type="primary"):
        # Format payload for bulk submit
        bulk_payload = {
            "payments": [
                {
                    "tracking_code": item['tracking_code'],
                    "contract_tracking_code": item['contract_tracking_code'],
                    "amount": item['amount'],
                    "series": item['series'],
                    "payment_year": item['payment_year'],
                    "funding_year": item['funding_year']
                } for item in st.session_state.payment_cart
            ]
        }
        
        try:
            submit_res = requests.post(f"{API_URL}/payments/bulk-submit", json=bulk_payload)
            if submit_res.status_code == 201:
                submitted_count = submit_res.json().get("submitted_count", 0)
                st.success(f"🎉 لیست با موفقیت نهایی شد! {submitted_count} قلم پرداخت ثبت و قفل گردید.")
                st.session_state.payment_cart = [] # Clear cart on success
            else:
                st.error(f"❌ خطا در ثبت نهایی: {submit_res.json().get('detail')}")
        except Exception as e:
            st.error(f"خطا در ارسال نهایی به سرور: {e}")
else:
    st.info("لیست پیش‌نویس در حال حاضر خالی است. ردیف‌های پرداخت را از بخش بالا اضافه کنید.")

## File: dashboard\views\contract_entry_page.py
------------------------------
"""Render the Phase 4 contract registration form."""

import re
from pathlib import Path
from uuid import uuid4

import jdatetime
import requests
import streamlit as st

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


def _parse_jalali_date(value: str) -> str:
    """Parse a strict Jalali date and return its Gregorian ISO representation."""
    date_parts = re.split(r"[/-]", value.strip())
    if len(date_parts) != 3 or any(not part.isdigit() for part in date_parts):
        raise ValueError("Invalid Jalali date format")

    year, month, day = (int(part) for part in date_parts)
    jalali_date = jdatetime.date(year, month, day)
    return jalali_date.togregorian().isoformat()


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
    """Extract an API error detail while tolerating non-JSON responses."""
    try:
        return response.json().get("detail", "خطای ناشناخته.")
    except ValueError:
        return "خطای ناشناخته."


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
            contract_date_iso = _parse_jalali_date(contract_date_str)
        except (TypeError, ValueError, OverflowError):
            st.error("فرمت یا مقدار تاریخ نامعتبر است. تاریخ را به صورت YYYY/MM/DD وارد کنید.")
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
from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database import Base
from models.employer import SoftDeleteMixin


class AnnualMandate(SoftDeleteMixin, Base):
    """Master table tracking mandated budget amounts per employer per fiscal year."""
    __tablename__ = 'annual_mandates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(String(20), ForeignKey('employers.classification_code', ondelete='CASCADE'), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False, index=True)
    mandated_amount = Column(Numeric(22, 0), nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('employer_code', 'fiscal_year', name='uq_employer_year_mandate'),
    )

    def __repr__(self):
        return f"<AnnualMandate(employer={self.employer_code}, year={self.fiscal_year}, amount={self.mandated_amount})>"


class DepositReceipt(SoftDeleteMixin, Base):
    """Detail table tracking individual deposit receipts per employer per fiscal year."""
    __tablename__ = 'deposit_receipts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employer_code = Column(String(20), ForeignKey('employers.classification_code', ondelete='CASCADE'), nullable=False, index=True)
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
from sqlalchemy import Column, String, Boolean, CheckConstraint
from core.database import Base

class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

class Employer(SoftDeleteMixin, Base):
    __tablename__ = 'employers'

    classification_code = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    employer_type = Column(String(20), nullable=False)
    parent_code = Column(String(20), nullable=True)
    province = Column(String(50), nullable=False)
    affairs_category = Column(String(100), nullable=True)
    upper_organization = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default='Active')

    __table_args__ = (
        CheckConstraint("employer_type IN ('Mother', 'Subsidiary', 'Independent')", name="check_employer_type"),
        CheckConstraint("status IN ('Active', 'Inactive')", name="check_employer_status"),
    )

## File: models\payment.py
------------------------------
from sqlalchemy import Column, String, ForeignKey, Date, Numeric, Integer
from core.database import Base
from models.employer import SoftDeleteMixin


class Payment(SoftDeleteMixin, Base):
    __tablename__ = 'payments'

    tracking_code = Column(String(50), primary_key=True)
    contract_tracking_code = Column(String(50), ForeignKey('contracts.tracking_code'), nullable=False)
    series = Column(String(50), nullable=True)
    amount = Column(Numeric(22, 0), nullable=False)  # Base Rials
    notification_letter_number = Column(String(100), nullable=True)
    notification_date = Column(Date, nullable=True)
    payment_year = Column(Integer, nullable=False)  # Cash flow year
    funding_year = Column(Integer, nullable=False)  # Budget consumption year
    attachment_path = Column(String(255), nullable=True)


## File: models\researchers.py
------------------------------
from sqlalchemy import Column, ForeignKey, String

from core.database import Base
from models.employer import SoftDeleteMixin


class Researcher(SoftDeleteMixin, Base):
    __tablename__ = "researchers"

    national_code = Column(String(10), primary_key=True)
    tracking_code = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    mobile = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    academic_rank = Column(String(50), nullable=True)
    university_id = Column(String(20), ForeignKey("universities.national_id"), nullable=False)
    education_level = Column(String(50), nullable=True)
    researcher_type = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="Active")


## File: models\transfer.py
------------------------------
"""
Credit Transfer Model
Junction table for allocating unspent funds from employers to specific contracts
"""

from sqlalchemy import Column, Integer, String, Numeric, Text, ForeignKey
from core.database import Base
from models.employer import SoftDeleteMixin


class CreditTransfer(Base, SoftDeleteMixin):
    """
    Credit Transfer model - tracks fund transfers between employers.
    Allows allocation of unspent funds from various employers to contracts
    managed by a central Secretariat without altering core deposit/payment tables.
    """
    __tablename__ = 'credit_transfers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Source employer (where funds come from)
    source_employer_code = Column(
        String,
        ForeignKey('employers.classification_code'),
        nullable=False,
        index=True
    )
    
    # Destination employer (where funds go to, default is Secretariat)
    destination_employer_code = Column(
        String,
        ForeignKey('employers.classification_code'),
        nullable=False,
        default='128342',
        index=True
    )
    
    # Optional broker facilitating the transfer
    broker_name = Column(String, nullable=True)
    
    # Fiscal year the funds originated from
    fiscal_year = Column(Integer, nullable=False, index=True)
    
    # Transfer amount in Rials
    amount = Column(Numeric(22, 0), nullable=False)
    
    # Contract receiving the transferred funds
    contract_tracking_code = Column(
        String,
        ForeignKey('contracts.tracking_code'),
        nullable=False,
        index=True
    )
    
    # Supporting documentation or notes
    documentation = Column(Text, nullable=True)
    
    def __repr__(self):
        return (
            f"<CreditTransfer(id={self.id}, "
            f"from={self.source_employer_code}, "
            f"to={self.destination_employer_code}, "
            f"amount={self.amount}, "
            f"year={self.fiscal_year})>"
        )


## File: models\university.py
------------------------------
from sqlalchemy import Column, String, Text
from core.database import Base
from models.employer import SoftDeleteMixin


class University(SoftDeleteMixin, Base):
    """University/Executing Institution model"""
    __tablename__ = 'universities'
    
    national_id = Column(String(20), primary_key=True, comment='شناسه ملی موسسه')
    tracking_code = Column(String(50), nullable=True, comment='کد رهگیری')
    name = Column(String(200), nullable=False, comment='نام موسسه')
    city = Column(String(100), nullable=True, comment='شهر')
    address = Column(Text, nullable=True, comment='آدرس')
    province = Column(String(50), nullable=False, comment='استان موسسه')
    university_type = Column(String(100), nullable=False, comment='نوع موسسه')
    status = Column(String(20), nullable=False, default='Active', comment='وضعیت')
    
    def __repr__(self):
        return f"<University(national_id='{self.national_id}', name='{self.name}')>"


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
    """Define the payload accepted when registering a new contract."""

    tracking_code: str = Field(
        ..., min_length=1, description="The contract tracking code (primary key)"
    )
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
    title: str = Field(
        ..., min_length=1, description="Contract or project title"
    )
    total_amount: float = Field(
        ..., gt=0, description="Total contract amount in Rials"
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
                "total_amount": 1000000000.0,
                "contract_date": "2024-03-20",
                "duration_months": 12,
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


class PaymentBatchValidationRequest(BaseModel):
    """
    Request schema for validating a single drafted (cart) payment.

    The `pending_cart_amount` represents the sum of other drafted payments that
    target the SAME employer inside the frontend's temporary cart. It is
    subtracted from the current database balance so that the available balance
    reflects funds already reserved by not-yet-submitted drafts.
    """
    contract_tracking_code: str = Field(..., description="The contract tracking code linked to the payment")
    amount: float = Field(..., description="The payment amount to be validated", gt=0)
    funding_year: int = Field(..., description="The funding year for the payment", ge=1300, le=1500)
    pending_cart_amount: float = Field(
        0.0,
        ge=0,
        description="Sum of other drafted payments for the same employer in the cart",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "contract_tracking_code": "CNT-1403-001",
                "amount": 50000000.0,
                "funding_year": 1403,
                "pending_cart_amount": 20000000.0,
            }
        }


class PaymentBatchValidationResponse(BaseModel):
    """
    Response schema returned when a drafted payment passes validation.
    """
    employer_code: str = Field(..., description="The employer classification code")
    current_db_balance: float = Field(..., description="Current balance from the database")
    pending_cart_amount: float = Field(..., description="Reserved amount from other drafts in the cart")
    available_balance: float = Field(..., description="Balance available after reserving cart drafts")
    amount: float = Field(..., description="The payment amount being validated")
    remaining_balance: float = Field(..., description="Available balance after this payment")
    is_valid: bool = Field(True, description="Whether the drafted payment is valid")


class PaymentBulkItem(BaseModel):
    """
    Single payment entry inside a bulk submission.
    """
    tracking_code: str = Field(..., description="Unique payment tracking code")
    contract_tracking_code: str = Field(..., description="Contract tracking code linked to the payment")
    amount: float = Field(..., description="Payment amount in base Rials", gt=0)
    payment_year: int = Field(..., description="Cash flow year", ge=1300, le=1500)
    funding_year: int = Field(..., description="Budget consumption year", ge=1300, le=1500)
    series: Optional[str] = Field(default=None, description="Payment series identifier")
    notification_letter_number: Optional[str] = Field(
        default=None,
        description="Notification letter number (optional; may be filled later via update form)",
    )
    notification_date: Optional[date] = Field(
        default=None,
        description="Notification date (optional; may be filled later via update form)",
    )
    attachment_path: Optional[str] = Field(default=None, description="Path to the payment attachment")

    class Config:
        json_schema_extra = {
            "example": {
                "tracking_code": "PAY-1403-0001",
                "contract_tracking_code": "CNT-1403-001",
                "amount": 50000000.0,
                "payment_year": 1403,
                "funding_year": 1403,
                "series": "Q1",
                "notification_letter_number": None,
                "notification_date": None,
                "attachment_path": None,
            }
        }


class PaymentBulkCreate(BaseModel):
    """
    Request schema for submitting a batch (cart) of payments at once.
    """
    payments: List[PaymentBulkItem] = Field(
        ..., min_length=1, description="List of payments to register in a single transaction"
    )


class PaymentBulkCreateResponse(BaseModel):
    """
    Response schema returned after a successful bulk submission.
    """
    message: str = Field(..., description="Human readable success message")
    submitted_count: int = Field(..., description="Number of payments committed")
    tracking_codes: List[str] = Field(..., description="Tracking codes of the committed payments")
    warning_messages: List[str] = Field(
        default_factory=list,
        description="Non-blocking FR-20 warnings for negative employer balances",
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
import jdatetime
from decimal import Decimal

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text
from core.database import engine, Base
from models.contract import Contract
from models.employer import Employer
from models.university import University
from models.researchers import Researcher


def parse_persian_date(date_str):
    """Parse Persian date string (e.g., '1400/05/05') to Gregorian date"""
    if pd.isna(date_str) or not date_str:
        return None
    
    try:
        # Remove any whitespace
        date_str = str(date_str).strip()
        # Parse Persian date and convert to Gregorian
        persian_date = jdatetime.datetime.strptime(date_str, '%Y/%m/%d')
        return persian_date.togregorian().date()
    except Exception as e:
        print(f"  [WARNING] Invalid date format: {date_str} - {e}")
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
            code for (code,) in session.query(Employer.classification_code).all()
        )
        print(f"[OK] Found {len(valid_employer_codes)} valid employer codes")
        
        valid_university_ids = set(
            uid for (uid,) in session.query(University.national_id).all()
        )
        print(f"[OK] Found {len(valid_university_ids)} valid university IDs")
        
        valid_researcher_ids = set(
            rid for (rid,) in session.query(Researcher.national_code).all()
        )
        print(f"[OK] Found {len(valid_researcher_ids)} valid researcher IDs")
        
        # Query existing tracking codes to avoid duplicates
        existing_tracking_codes = set(
            code for (code,) in session.query(Contract.tracking_code).all()
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
import jdatetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import engine, Base
from models.payment import Payment
from models.contract import Contract


def parse_jalali_date(date_str):
    """Convert Jalali date string (YYYY/MM/DD) to Gregorian date object."""
    if pd.isna(date_str) or date_str == '' or date_str is None:
        return None
    
    try:
        date_str = str(date_str).strip()
        parts = date_str.split('/')
        if len(parts) != 3:
            return None
        
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        jalali_date = jdatetime.date(year, month, day)
        gregorian_date = jalali_date.togregorian()
        return gregorian_date
    except (ValueError, AttributeError, IndexError):
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
        valid_contracts = set(session.query(Contract.tracking_code).all())
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

    This function implements FR-18, FR-19, and FR-20. A negative projected
    balance is reported through ``is_negative`` and never raises an error.

    Args:
        db: Active SQLAlchemy database session.
        contract_code: Contract tracking code linked to the payment.
        payment_amount: Payment amount in base Rials.
        funding_year: Funding year for the payment.
        lock_rows: When true, lock the active contract and employer rows for
            the duration of the caller's transaction.

    Returns:
        A dictionary containing employer code, current balance, payment amount,
        projected balance, and whether the projected balance is negative.

    Raises:
        ValueError: If the contract or linked employer is missing or soft-deleted.
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

    return {
        "employer_code": employer_code,
        "current_balance": current_balance,
        "payment_amount": payment_amount,
        "new_balance": new_balance,
        "is_negative": new_balance < 0,
    }


