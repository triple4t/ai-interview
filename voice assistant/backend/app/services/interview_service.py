import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.qa import QAPair
from app.models.interview import InterviewResult
from app.schemas.interview import InterviewResultResponse, ConversationMessage
from app.services.rag_service import rag_service
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json

class InterviewService:
    def __init__(self):
        # Initialize Azure OpenAI for evaluation
        self.model = None
        if rag_service.azure_configured:
            try:
                self.model = AzureChatOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
                )
            except Exception as e:
                print(f"Error initializing interview service model: {e}")
        
        # Evaluation prompts
        self.evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert technical interviewer and evaluator. Your task is to evaluate interview responses and provide detailed feedback.

IMPORTANT: This interview consists of EXACTLY 5 questions. Evaluate all 5 Q&A pairs.

EVALUATION CRITERIA:
1. Technical Accuracy (30%): How correct and accurate are the technical concepts?
2. Depth of Knowledge (25%): How well does the candidate demonstrate understanding?
3. Communication Clarity (20%): How clearly and effectively is the response communicated?
4. Problem-Solving Approach (15%): How logical and systematic is the approach?
5. Practical Application (10%): How well does the candidate apply concepts to real scenarios?

SCORING GUIDELINES:
- 90-100: Exceptional - Comprehensive, accurate, well-communicated
- 80-89: Excellent - Strong understanding with minor gaps
- 70-79: Good - Solid understanding with some areas for improvement
- 60-69: Satisfactory - Basic understanding with notable gaps
- 50-59: Needs Improvement - Limited understanding
- Below 50: Poor - Significant misunderstandings or lack of knowledge

INTERVIEW DATA (5 Questions):
Questions: {questions}
Answers: {answers}
Full Conversation: {conversation}

Provide evaluation in the following JSON format:
{{
    "overall_score": <total_score_out_of_100>,
    "overall_analysis": "<comprehensive analysis of the 5-question interview>",
    "detailed_feedback": [
        {{
            "question": "<question 1>",
            "answer": "<answer 1>",
            "score": <score_out_of_100>,
            "feedback": "<detailed feedback for question 1>",
            "strengths": ["<strength1>", "<strength2>"],
            "weaknesses": ["<weakness1>", "<weakness2>"]
        }},
        {{
            "question": "<question 2>",
            "answer": "<answer 2>",
            "score": <score_out_of_100>,
            "feedback": "<detailed feedback for question 2>",
            "strengths": ["<strength1>", "<strength2>"],
            "weaknesses": ["<weakness1>", "<weakness2>"]
        }},
        {{
            "question": "<question 3>",
            "answer": "<answer 3>",
            "score": <score_out_of_100>,
            "feedback": "<detailed feedback for question 3>",
            "strengths": ["<strength1>", "<strength2>"],
            "weaknesses": ["<weakness1>", "<weakness2>"]
        }},
        {{
            "question": "<question 4>",
            "answer": "<answer 4>",
            "score": <score_out_of_100>,
            "feedback": "<detailed feedback for question 4>",
            "strengths": ["<strength1>", "<strength2>"],
            "weaknesses": ["<weakness1>", "<weakness2>"]
        }},
        {{
            "question": "<question 5>",
            "answer": "<answer 5>",
            "score": <score_out_of_100>,
            "feedback": "<detailed feedback for question 5>",
            "strengths": ["<strength1>", "<strength2>"],
            "weaknesses": ["<weakness1>", "<weakness2>"]
        }}
    ],
    "strengths": ["<overall_strength1>", "<overall_strength2>"],
    "areas_for_improvement": ["<area1>", "<area2>"],
    "recommendations": ["<recommendation1>", "<recommendation2>"]
}}

Return only valid JSON."""),
            ("user", "Evaluate this 5-question technical interview session.")
        ])

    async def evaluate_session(
        self,
        user_id: int,
        session_id: str,
        conversation: List[ConversationMessage],
        questions: List[str],
        answers: List[str],
        db: Session
    ) -> InterviewResultResponse:
        """
        Evaluate a complete interview session with exactly 5 questions
        """
        # Ensure we only evaluate exactly 5 questions
        if len(questions) != 5 or len(answers) != 5:
            print(f"⚠️ Warning: Expected 5 Q&A pairs, got {len(questions)} questions and {len(answers)} answers")
            # Pad with empty strings if needed
            while len(questions) < 5:
                questions.append("No question provided")
            while len(answers) < 5:
                answers.append("No answer provided")
            # Truncate if more than 5
            questions = questions[:5]
            answers = answers[:5]
        """
        Evaluate a complete interview session
        """
        try:
            # Format conversation for evaluation
            conversation_text = "\n".join([
                f"{msg.role.upper()}: {msg.content}" 
                for msg in conversation
            ])
            
            # Prepare questions and answers
            qa_text = "\n\n".join([
                f"Q{i+1}: {q}\nA{i+1}: {a}"
                for i, (q, a) in enumerate(zip(questions, answers))
            ])
            
            # Get AI evaluation
            if self.model:
                chain = self.evaluation_prompt | self.model
                response = chain.invoke({
                    "questions": questions,
                    "answers": answers,
                    "conversation": conversation_text
                })
                
                # Parse JSON response
                try:
                    content = response.content.strip()
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.startswith('```'):
                        content = content[3:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()
                    
                    evaluation = json.loads(content)
                    
                    # Create detailed feedback for each Q&A
                    detailed_feedback = []
                    for i, (q, a) in enumerate(zip(questions, answers)):
                        if i < len(evaluation.get("detailed_feedback", [])):
                            feedback_item = evaluation["detailed_feedback"][i]
                        else:
                            # Fallback if detailed feedback is missing
                            feedback_item = {
                                "question": q,
                                "answer": a,
                                "score": evaluation.get("overall_score", 0) // len(questions),
                                "feedback": "Evaluation completed",
                                "strengths": [],
                                "weaknesses": []
                            }
                        detailed_feedback.append(feedback_item)
                    
                    # Calculate scores
                    total_score = evaluation.get("overall_score", 0)
                    max_score = 100
                    percentage = (total_score / max_score) * 100
                    
                    # Create result
                    result = InterviewResultResponse(
                        session_id=session_id,
                        user_id=user_id,
                        total_score=total_score,
                        max_score=max_score,
                        percentage=percentage,
                        questions_evaluated=len(questions),
                        overall_analysis=evaluation.get("overall_analysis", "Evaluation completed"),
                        detailed_feedback=detailed_feedback,
                        strengths=evaluation.get("strengths", []),
                        areas_for_improvement=evaluation.get("areas_for_improvement", []),
                        recommendations=evaluation.get("recommendations", []),
                        transcript=[{"role": msg.role, "content": msg.content, "timestamp": msg.timestamp} for msg in conversation],
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    # Store in database
                    storage_success = await self._store_evaluation_result(result, db)
                    if not storage_success:
                        print("⚠️ Warning: Failed to store evaluation result in database")
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
                    print(f"Raw response: {response.content}")
                    return self._create_fallback_result(session_id, user_id, questions, answers)
            
            else:
                # Fallback when AI model is not available
                return self._create_fallback_result(session_id, user_id, questions, answers)
                
        except Exception as e:
            print(f"Error in interview evaluation: {e}")
            return self._create_fallback_result(session_id, user_id, questions, answers)

    def _create_fallback_result(
        self,
        session_id: str,
        user_id: int,
        questions: List[str],
        answers: List[str]
    ) -> InterviewResultResponse:
        """
        Create a fallback result when AI evaluation is not available
        """
        # Simple scoring based on answer length and content
        scores = []
        for answer in answers:
            # Basic scoring: longer, more detailed answers get higher scores
            base_score = min(len(answer.split()) * 2, 80)  # Max 80 for length
            if any(keyword in answer.lower() for keyword in ['because', 'example', 'specifically', 'however']):
                base_score += 10  # Bonus for detailed explanations
            scores.append(min(base_score, 100))
        
        total_score = sum(scores) // len(scores) if scores else 50
        max_score = 100
        percentage = (total_score / max_score) * 100
        
        detailed_feedback = []
        for i, (q, a) in enumerate(zip(questions, answers)):
            detailed_feedback.append({
                "question": q,
                "answer": a,
                "score": scores[i] if i < len(scores) else 50,
                "feedback": "Basic evaluation completed",
                "strengths": ["Answered the question"],
                "weaknesses": ["Detailed AI evaluation not available"]
            })
        
        return InterviewResultResponse(
            session_id=session_id,
            user_id=user_id,
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            questions_evaluated=len(questions),
            overall_analysis="Basic evaluation completed. AI evaluation not available.",
            detailed_feedback=detailed_feedback,
            strengths=["Completed the interview"],
            areas_for_improvement=["Enable AI evaluation for detailed feedback"],
            recommendations=["Ensure Azure OpenAI is configured for detailed evaluation"],
            transcript=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    async def _store_evaluation_result(
        self,
        result: InterviewResultResponse,
        db: Session
    ):
        """
        Store or update evaluation result in database based on session_id
        """
        try:
            # Check if a record with this session_id already exists
            existing_result = db.query(InterviewResult).filter(
                InterviewResult.session_id == result.session_id
            ).first()

            # Ensure transcript timestamps are serializable
            transcript = []
            if result.transcript:
                for msg in result.transcript:
                    msg_copy = msg.copy()
                    if 'timestamp' in msg_copy and isinstance(msg_copy['timestamp'], datetime):
                        msg_copy['timestamp'] = msg_copy['timestamp'].isoformat()
                    transcript.append(msg_copy)
            else:
                transcript = None

            # Ensure all JSON fields are serializable
            def make_serializable(obj):
                if isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_serializable(item) for item in obj]
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                return obj

            current_time = datetime.now()
            
            if existing_result:
                # Update existing record
                existing_result.total_score = result.total_score
                existing_result.max_score = result.max_score
                existing_result.percentage = result.percentage
                existing_result.questions_evaluated = result.questions_evaluated
                existing_result.overall_analysis = result.overall_analysis
                existing_result.detailed_feedback = make_serializable(result.detailed_feedback)
                existing_result.strengths = make_serializable(result.strengths)
                existing_result.areas_for_improvement = make_serializable(result.areas_for_improvement)
                existing_result.recommendations = make_serializable(result.recommendations)
                existing_result.transcript = transcript
                existing_result.updated_at = current_time
                
                db.add(existing_result)
                db.commit()
                db.refresh(existing_result)
                
                print(f"✅ Updated evaluation result for session {result.session_id}")
            else:
                # Create new record
                interview_result = InterviewResult(
                    session_id=result.session_id,
                    user_id=result.user_id,
                    total_score=result.total_score,
                    max_score=result.max_score,
                    percentage=result.percentage,
                    questions_evaluated=result.questions_evaluated,
                    overall_analysis=result.overall_analysis,
                    detailed_feedback=make_serializable(result.detailed_feedback),
                    strengths=make_serializable(result.strengths),
                    areas_for_improvement=make_serializable(result.areas_for_improvement),
                    recommendations=make_serializable(result.recommendations),
                    transcript=transcript,
                    created_at=result.created_at or current_time,
                    updated_at=current_time
                )
                
                db.add(interview_result)
                db.commit()
                db.refresh(interview_result)
                
                print(f"✅ Created new evaluation result for session {result.session_id}")
            
            return True
            
        except Exception as e:
            print(f"Error storing evaluation result: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return False

    async def get_user_history(
        self,
        user_id: int,
        db: Session
    ) -> List[InterviewResultResponse]:
        """
        Get user's interview history with proper datetime handling
        """
        try:
            # Get complete evaluation results from the new table
            interview_results = db.query(InterviewResult).filter(
                InterviewResult.user_id == user_id
            ).order_by(InterviewResult.created_at.desc()).all()
            
            results = []
            for result in interview_results:
                # Ensure we have valid timestamps
                created_at = result.created_at or datetime.now()
                updated_at = result.updated_at or created_at
                
                interview_result = InterviewResultResponse(
                    session_id=result.session_id,
                    user_id=result.user_id,
                    total_score=result.total_score,
                    max_score=result.max_score,
                    percentage=result.percentage,
                    questions_evaluated=result.questions_evaluated,
                    overall_analysis=result.overall_analysis or "No analysis available",
                    detailed_feedback=result.detailed_feedback or [],
                    strengths=result.strengths or [],
                    areas_for_improvement=result.areas_for_improvement or [],
                    recommendations=result.recommendations or [],
                    transcript=result.transcript or [],
                    created_at=created_at,
                    updated_at=updated_at
                )
                results.append(interview_result)
            
            return results
            
        except Exception as e:
            print(f"Error getting user history: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_session_result(
        self,
        session_id: str,
        user_id: int,
        db: Session
    ) -> Optional[InterviewResultResponse]:
        """
        Get specific session result with proper datetime handling
        """
        try:
            result = db.query(InterviewResult).filter(
                InterviewResult.session_id == session_id,
                InterviewResult.user_id == user_id
            ).first()
            
            if not result:
                return None
            
            # Ensure we have valid timestamps
            created_at = result.created_at or datetime.now()
            updated_at = result.updated_at or created_at
            
            return InterviewResultResponse(
                session_id=result.session_id,
                user_id=result.user_id,
                total_score=result.total_score,
                max_score=result.max_score,
                percentage=result.percentage,
                questions_evaluated=result.questions_evaluated,
                overall_analysis=result.overall_analysis,
                detailed_feedback=result.detailed_feedback or [],
                strengths=result.strengths or [],
                areas_for_improvement=result.areas_for_improvement or [],
                recommendations=result.recommendations or [],
                transcript=result.transcript or [],
                created_at=created_at,
                updated_at=updated_at
            )
            
        except Exception as e:
            print(f"Error getting session result: {e}")
            import traceback
            traceback.print_exc()
            return None 