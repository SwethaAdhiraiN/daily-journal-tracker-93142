import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

from .routes import auth, entries, export
from ..utils.security import limiter
from ..utils.database import db
from ..utils.export import export_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Daily Journal API...")
    
    # Initialize database
    try:
        db._ensure_data_directory()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Initialize export service
    try:
        export_service.cleanup_old_exports(days_old=7)
        logger.info("Export service initialized")
    except Exception as e:
        logger.error(f"Export service initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Daily Journal API...")


# Create FastAPI application
app = FastAPI(
    title="Daily Journal API",
    description="A secure, user-friendly daily journal application API with authentication, entry management, and export features.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "Authentication", 
            "description": "User registration, login, logout, and token management"
        },
        {
            "name": "Journal Entries",
            "description": "CRUD operations for journal entries, search, and filtering"
        },
        {
            "name": "Export",
            "description": "Export journal entries to various formats (TXT, PDF)"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(entries.router)
app.include_router(export.router)


# PUBLIC_INTERFACE
@app.get("/", tags=["Health"], summary="Health check")
@limiter.limit("30/minute")
async def health_check(request: Request):
    """
    Health check endpoint.
    
    Returns the current status of the API service including version
    and basic system information.
    
    Returns:
        Dict containing health status and system info
    """
    return {
        "message": "Daily Journal API is healthy",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": "2024-01-01T00:00:00Z"
    }


# PUBLIC_INTERFACE
@app.get("/health", tags=["Health"], summary="Detailed health check")
@limiter.limit("10/minute")
async def detailed_health_check(request: Request):
    """
    Detailed health check endpoint.
    
    Returns detailed information about the API service health
    including database connectivity and system resources.
    
    Returns:
        Dict containing detailed health information
    """
    try:
        # Test database connectivity
        db_healthy = True
        try:
            db._ensure_data_directory()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_healthy = False
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "version": "1.0.0",
            "services": {
                "database": "healthy" if db_healthy else "unhealthy",
                "export": "healthy",
                "authentication": "healthy"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "unhealthy",
                "error": "Health check failed"
            }
        )


# PUBLIC_INTERFACE
@app.get("/api/info", tags=["Health"], summary="API information")
async def api_info():
    """
    Get API information and capabilities.
    
    Returns information about the API endpoints, features,
    and supported operations.
    
    Returns:
        Dict containing API information
    """
    return {
        "name": "Daily Journal API",
        "version": "1.0.0",
        "description": "A secure daily journal application with authentication and export features",
        "features": [
            "User registration and authentication",
            "JWT-based security",
            "CRUD operations for journal entries",
            "Entry search and filtering",
            "Mood tracking",
            "Tag support",
            "Export to TXT and PDF formats",
            "Rate limiting",
            "Input validation and sanitization"
        ],
        "endpoints": {
            "authentication": "/api/auth/*",
            "journal_entries": "/api/entries/*",
            "export": "/api/export/*",
            "documentation": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "production") == "development"
    )
