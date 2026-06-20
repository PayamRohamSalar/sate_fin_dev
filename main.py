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
