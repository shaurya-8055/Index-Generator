"""API routers."""

from fastapi import APIRouter

from app.api import auth_routes, documents, indexes

api_router = APIRouter()
api_router.include_router(auth_routes.router)
api_router.include_router(documents.router)
api_router.include_router(indexes.router)

__all__ = ["api_router"]
