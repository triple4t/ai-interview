from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user, get_optional_user
from app.services.rag_service import rag_service
from app.services.interview_service import InterviewService
from app.schemas.interview import InterviewSessionCreate, InterviewResultResponse
from typing import List, Dict, Any, Optional
import json

router = APIRouter(prefix="/interview", tags=["interview"])

@router.post("/evaluate", response_model=InterviewResultResponse)
async def evaluate_interview(
    session_data: InterviewSessionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Evaluate a complete interview session and return detailed results
    """
    try:
        # Create interview service instance
        interview_service = InterviewService()
        
        # Use a default user ID if not authenticated
        user_id = current_user.id if current_user else 1
        
        # Process the interview session
        result = await interview_service.evaluate_session(
            user_id=user_id,
            session_id=session_data.session_id,
            conversation=session_data.conversation,
            questions=session_data.questions,
            answers=session_data.answers,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating interview: {str(e)}"
        )

@router.get("/history", response_model=List[InterviewResultResponse])
async def get_interview_history(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get user's interview history
    """
    try:
        interview_service = InterviewService()
        user_id = current_user.id if current_user else 1
        history = await interview_service.get_user_history(
            user_id=user_id,
            db=db
        )
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching interview history: {str(e)}"
        )

@router.get("/{session_id}", response_model=InterviewResultResponse)
async def get_interview_result(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get specific interview result by session ID
    """
    try:
        interview_service = InterviewService()
        user_id = current_user.id if current_user else 1
        result = await interview_service.get_session_result(
            session_id=session_id,
            user_id=user_id,
            db=db
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Interview session not found"
            )
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching interview result: {str(e)}"
        ) 