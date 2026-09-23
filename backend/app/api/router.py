from fastapi import APIRouter

from backend.app.api.v1 import (
    auth,
    cases,
    datasets,
    runs,
    alerts,
    wallets,
    graph,
    reports,
    feedback,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(datasets.router, tags=["datasets"])
api_router.include_router(runs.router, tags=["runs"])
api_router.include_router(alerts.router, tags=["alerts"])
api_router.include_router(wallets.router, tags=["wallets"])
api_router.include_router(graph.router, tags=["graph"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(feedback.router, tags=["feedback"])
