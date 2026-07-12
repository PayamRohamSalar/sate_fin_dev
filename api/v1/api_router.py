from fastapi import APIRouter

from api.v1.endpoints import contracts, employers, payments

# Create the main API router for version 1
api_router = APIRouter()

# Include sub-routers for different endpoint groups
api_router.include_router(employers.router)
api_router.include_router(payments.router)
api_router.include_router(contracts.router)

# Future routers can be added here as the system grows:
# api_router.include_router(deposits.router)
