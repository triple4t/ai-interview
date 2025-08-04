from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.resume import router as resume_router
from app.api.qa import router as qa_router
from app.api.interview import router as interview_router
from app.api.face_detection import router as face_detection_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(resume_router)
api_router.include_router(qa_router)
api_router.include_router(interview_router)
api_router.include_router(face_detection_router)
