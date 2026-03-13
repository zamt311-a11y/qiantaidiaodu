from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, route_plans, sectors, stats, tasks, users


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(sectors.router, prefix="/sectors", tags=["sectors"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(route_plans.router, prefix="/route_plans", tags=["route_plans"])

