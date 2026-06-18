from fastapi import APIRouter
from app.api import auth, users, essays, scoring, vocabulary, errors, feedback, learning, admin, models

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(essays.router, prefix="/essays", tags=["essays"])
api_router.include_router(scoring.router, prefix="/essays", tags=["scoring"])
api_router.include_router(vocabulary.router, prefix="/vocabulary", tags=["vocabulary"])
api_router.include_router(errors.router, prefix="/essays", tags=["errors"])
api_router.include_router(feedback.router, prefix="/essays", tags=["feedback"])
api_router.include_router(learning.router, prefix="/learning", tags=["learning"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
