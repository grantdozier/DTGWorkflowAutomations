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


# Import and include routers
from app.api.v1.endpoints import auth, company, project, document, ai, estimation, equipment, vendor, import_data, quotes, quote_requests, discrepancies, specifications, materials, matching, estimate_generation, generated_quotes

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(company.router, prefix="/api/v1/company", tags=["company"])
app.include_router(project.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(document.router, prefix="/api/v1", tags=["documents"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(estimation.router, prefix="/api/v1", tags=["estimation"])
app.include_router(estimate_generation.router, prefix="/api/v1/estimates", tags=["estimate-generation"])
app.include_router(materials.router, prefix="/api/v1/materials", tags=["materials"])
app.include_router(matching.router, prefix="/api/v1/matching", tags=["matching"])
app.include_router(equipment.router, prefix="/api/v1/equipment", tags=["equipment"])
app.include_router(vendor.router, prefix="/api/v1/vendors", tags=["vendors"])
app.include_router(import_data.router, prefix="/api/v1/import", tags=["import"])
app.include_router(quotes.router, prefix="/api/v1", tags=["quotes"])
app.include_router(quote_requests.router, prefix="/api/v1", tags=["quote-requests"])
app.include_router(discrepancies.router, prefix="/api/v1", tags=["discrepancies"])
app.include_router(specifications.router, prefix="/api/v1", tags=["specifications"])
app.include_router(generated_quotes.router, prefix="/api/v1", tags=["generated-quotes"])
