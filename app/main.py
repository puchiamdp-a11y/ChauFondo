from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.auth.routes import router as auth_router
from app.images.routes import router as images_router
from app.payments.routes import router as payments_router

app = FastAPI(
    title="ChauFondo API",
    description="Backend for ChauFondo - Image Background Removal Service",
    version="1.0.0",
)

origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(images_router)
app.include_router(payments_router)


@app.get("/health")
def health_check():
    """Health check endpoint to verify API and database connectivity."""
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "ok", "db": "disconnected", "error": str(e)}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Welcome to ChauFondo API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
