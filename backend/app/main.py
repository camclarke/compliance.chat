from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.core.config import settings

def create_app() -> FastAPI:
    """
    Application factory pattern for creating the FastAPI app instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Backend API for the compliance.chat multi-agent RAG system."
    )

    # Configure CORS for local frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Update this to the specific frontend URL in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(chat_router, prefix="/api", tags=["Chat"])

    @app.get("/")
    def health_check():
        return {"status": "healthy", "service": settings.PROJECT_NAME}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
