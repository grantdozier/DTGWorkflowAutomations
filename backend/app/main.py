from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import engine, Base

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "plans"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "specs"), exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Import and include routers (will add after creating models and endpoints)
# from app.api.v1 import auth, projects, companies
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
# app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
