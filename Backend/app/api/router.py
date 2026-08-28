from fastapi import APIRouter

from app.api.admin.router import router as admin_router
from app.api.auth.router import router as auth_router
from app.api.businesses import router as businesses_router
from app.api.citizen.router import router as citizen_router
from app.api.health import router as health_router
from app.api.inspector.router import router as inspector_router
from app.api.notifications import router as notifications_router
from app.api.officer.router import router as officer_router
from app.api.reference import router as reference_router

api_router = APIRouter()
api_router.include_router(health_router)

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth_router)
v1_router.include_router(admin_router)
v1_router.include_router(officer_router)
v1_router.include_router(inspector_router)
v1_router.include_router(citizen_router)
v1_router.include_router(businesses_router)
v1_router.include_router(reference_router)
v1_router.include_router(notifications_router)

api_router.include_router(v1_router)
