import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.billing import router as billing_router
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialises the AIProjectClient once at startup and tears it down on shutdown.
    Sharing a single client across all requests avoids per-request auth overhead
    and connection-list scans for the Bing grounding tool.
    """
    from app.services.agent_orchestrator import create_kernel
    app.state.ai_client = await create_kernel()
    if app.state.ai_client:
        logger.info("AIProjectClient initialised and ready.")
    else:
        logger.error("AIProjectClient could not be initialised — AI features are disabled.")
    yield
    if getattr(app.state, "ai_client", None):
        await app.state.ai_client.close()
        logger.info("AIProjectClient closed.")


def create_app() -> FastAPI:
    """
    Application factory pattern for creating the FastAPI app instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Backend API for the compliance.chat Azure AI Agent Service.",
        lifespan=lifespan,
    )

    # Configure CORS for local frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Update to specific frontend URL in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(chat_router, prefix="/api", tags=["Chat"])
    app.include_router(billing_router, prefix="/api/billing", tags=["Billing"])

    @app.get("/")
    def health_check():
        return {"status": "healthy", "service": settings.PROJECT_NAME}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
