from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(
    title="Smart Internal Knowledge Base Assistant API",
    description="Backend API for an AI-powered internal company knowledge assistant.",
    version="0.1.0",
)

app.include_router(api_router)