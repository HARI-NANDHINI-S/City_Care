import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router


# --------------------------------------------------
# Create Database Tables
# --------------------------------------------------

Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# Create FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Public Infrastructure Issue Detection and Resolution Platform",
    
    # API Documentation
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)


# --------------------------------------------------
# CORS Configuration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Uploads Directory
# --------------------------------------------------

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory=settings.UPLOAD_DIR),
    name="uploads",
)


# --------------------------------------------------
# API Routes
# --------------------------------------------------

app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
)


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to CivicVision AI API",
        "version": settings.VERSION,
        "status": "running",
        "docs": f"{settings.API_V1_STR}/docs",
    }


from fastapi.responses import RedirectResponse

@app.get("/docs", include_in_schema=False)
def docs_redirect():
    return RedirectResponse(url=f"{settings.API_V1_STR}/docs")


@app.get("/redoc", include_in_schema=False)
def redoc_redirect():
    return RedirectResponse(url=f"{settings.API_V1_STR}/redoc")



# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "CivicVision AI Backend Engine",
        "version": settings.VERSION,
        "database": "connected",
    }


# --------------------------------------------------
# API Health Check
# --------------------------------------------------

@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def api_health_check():
    return {
        "status": "online",
        "service": "CivicVision AI Backend Engine",
        "version": settings.VERSION,
        "database": "connected",
    }


# --------------------------------------------------
# Run Application
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )