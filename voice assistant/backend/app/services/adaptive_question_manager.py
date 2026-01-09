from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import random
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class InterviewPhase(Enum):
    """Interview phases"""
    INTRODUCTION = "introduction"
    RESUME_DEEP_DIVE = "resume_deep_dive"
    TECHNICAL_QUESTIONS = "technical_questions"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"


class AnswerQuality(Enum):
    """Answer quality assessment"""
    EXCELLENT = "excellent"  # 80-100
    GOOD = "good"  # 60-79
    FAIR = "fair"  # 40-59
    POOR = "poor"  # 0-39


@dataclass
class QuestionContext:
    """Context for a question"""
    question: str
    question_type: str  # "file", "resume", "followup", "introduction"
    phase: InterviewPhase
    difficulty: str  # "easy", "medium", "hard"
    source: Optional[str] = None  # For resume questions, what part of resume
    asked_at: Optional[datetime] = None


@dataclass
class AnswerAssessment:
    """Assessment of an answer"""
    question: str
    answer: str
    quality: AnswerQuality
    score: float  # 0-100
    strengths: List[str]
    weaknesses: List[str]
    topics_covered: List[str]
    needs_followup: bool


class AdaptiveQuestionManager:
    """Manages adaptive question selection and generation"""
    
    def __init__(
        self,
        session_id: str,
        questions_pool: List[str],
        resume_data: Optional[Dict[str, Any]] = None,
        jd_requirements: Optional[Dict[str, Any]] = None,
        previous_topics: Optional[List[str]] = None
    ):
        self.session_id = session_id
        self.questions_pool = questions_pool
        self.resume_data = resume_data or {}
        self.jd_requirements = jd_requirements or {}
        self.previous_topics = set(previous_topics or [])
        
        # Calculate experience to determine if fresher
        self.experience_years = self._calculate_experience()
        self.is_fresher = 0 <= self.experience_years <= 2
        
        # Interview state
        self.current_phase = InterviewPhase.INTRODUCTION
        self.questions_asked: List[QuestionContext] = []
        self.answers_assessed: List[AnswerAssessment] = []
        self.used_questions = set()
        self.used_resume_questions = set()
        self.weak_areas: List[str] = []
        self.strong_areas: List[str] = []
        
        # Question counts
        self.intro_asked = False
        self.resume_questions_asked = 0
        self.technical_questions_asked = 0
        self.followup_questions_asked = 0
        
        # Target distribution (approximate)
        # Total ~10 questions: 1 intro + 2 resume + 7 technical + some followups
        self.target_resume_questions = 2  # ~20% of 10 total questions
        self.target_technical_questions = 7  # ~70% of 10 total questions
        self.target_followups = 1  # ~10% of 10 total questions
        
        # Difficulty tracking - start with "easy" for freshers (0-2 years)
        if self.is_fresher:
            self.current_difficulty = "easy"
            logger.info(f"[Adaptive] Candidate is fresher ({self.experience_years} years), starting with easy difficulty")
        else:
            self.current_difficulty = "medium"
        self.difficulty_history: List[Tuple[str, float]] = []  # (difficulty, score)
    
    def _calculate_experience(self) -> float:
        """Calculate experience years from resume data"""
        if not self.resume_data:
            return 0.0
        
        # First try explicit experience_years
        if self.resume_data.get("experience_years"):
            try:
                return float(self.resume_data["experience_years"])
            except (ValueError, TypeError):
                pass
        
        # Calculate from roles/experiences
        total_years = 0.0
        experiences = self.resume_data.get("experiences", [])
        roles = self.resume_data.get("roles", [])
        
        # Combine experiences and roles
        all_roles = experiences + roles
        
        if not all_roles:
            return 0.0
        
        # Calculate from role dates
        from datetime import datetime
        
        for role in all_roles:
            start_date = role.get("start_date") or role.get("start")
            end_date = role.get("end_date") or role.get("end") or "present"
            
            if start_date:
                try:
                    # Parse dates (simplified - handles YYYY-MM or YYYY-MM-DD)
                    if end_date.lower() == "present" or end_date.lower() == "current":
                        end_date_obj = datetime.now()
                    else:
                        # Try to parse date
                        date_parts = end_date.split("-")
                        if len(date_parts) >= 2:
                            end_date_obj = datetime(int(date_parts[0]), int(date_parts[1]), 1)
                        else:
                            end_date_obj = datetime(int(date_parts[0]), 1, 1)
                    
                    start_parts = start_date.split("-")
                    if len(start_parts) >= 2:
                        start_date_obj = datetime(int(start_parts[0]), int(start_parts[1]), 1)
                    else:
                        start_date_obj = datetime(int(start_parts[0]), 1, 1)
                    
                    # Calculate years difference
                    years_diff = (end_date_obj - start_date_obj).days / 365.25
                    total_years += max(0, years_diff)
                except (ValueError, TypeError, IndexError):
                    continue
        
        return round(total_years, 1)
    
    def get_next_question(self) -> Optional[QuestionContext]:
        """Get the next question based on current phase and state"""
        
        # Phase 1: Introduction (always first)
        if not self.intro_asked:
            self.intro_asked = True
            return QuestionContext(
                question="Could you please introduce yourself and tell me a bit about your background?",
                question_type="introduction",
                phase=InterviewPhase.INTRODUCTION,
                difficulty="easy",
                asked_at=datetime.now()
            )
        
        # Phase 2: Resume deep dive (20% of questions)
        if (self.resume_questions_asked < self.target_resume_questions and 
            self.current_phase in [InterviewPhase.INTRODUCTION, InterviewPhase.RESUME_DEEP_DIVE]):
            self.current_phase = InterviewPhase.RESUME_DEEP_DIVE
            question = self._generate_resume_question()
            if question:
                self.resume_questions_asked += 1
                return question
        
        # Phase 3: Technical questions (70% of questions)
        if (self.technical_questions_asked < self.target_technical_questions and
            (self.current_phase == InterviewPhase.RESUME_DEEP_DIVE or 
             self.current_phase == InterviewPhase.TECHNICAL_QUESTIONS)):
            self.current_phase = InterviewPhase.TECHNICAL_QUESTIONS
            question = self._get_technical_question()
            if question:
                self.technical_questions_asked += 1
                return question
        
        # Phase 4: Follow-ups (10% of questions, generated dynamically)
        if self.technical_questions_asked >= 3:  # Start follow-ups after some technical questions
            followup = self._generate_followup_question()
            if followup:
                self.followup_questions_asked += 1
                return followup
        
        # If we've asked enough questions, return None to signal completion
        total_asked = (self.resume_questions_asked + 
                      self.technical_questions_asked + 
                      self.followup_questions_asked)
        
        if total_asked >= 10:  # Total interview questions
            self.current_phase = InterviewPhase.CLOSING
            return None
        
        # Fallback: continue with technical questions
        question = self._get_technical_question()
        if question:
            self.technical_questions_asked += 1
            return question
        
        return None
    
    def _generate_resume_question(self) -> Optional[QuestionContext]:
        """Generate a question based on resume data"""
        if not self.resume_data:
            # If no resume data, skip resume questions and move to technical
            return None
        
        # Extract key information from resume
        experiences = self.resume_data.get("experiences", [])
        skills = self.resume_data.get("skills", [])
        projects = self.resume_data.get("projects", [])
        education = self.resume_data.get("education", [])
        
        # Generate question based on what's available
        resume_question_templates = []
        
        if experiences:
            latest_exp = experiences[0] if experiences else {}
            company = latest_exp.get('company', 'your previous company')
            title = latest_exp.get('title', 'a developer')
            resume_question_templates.extend([
                f"Tell me about your experience as {title} at {company}. What were your main responsibilities?",
                f"I see you worked at {company}. Can you walk me through a challenging project you worked on there?",
                f"What technologies did you use in your role at {company}?",
            ])
        
        if projects:
            latest_project = projects[0] if projects else {}
            project_name = latest_project.get('name', 'a project')
            resume_question_templates.extend([
                f"I noticed you worked on {project_name}. Can you tell me more about it?",
                f"What was your role in {project_name}? What challenges did you face?",
            ])
        
        if skills:
            top_skills = skills[:3] if len(skills) >= 3 else skills
            skill_str = ", ".join(top_skills)
            resume_question_templates.append(
                f"You mentioned {skill_str} in your resume. Can you tell me about your experience with these technologies?"
            )
        
        if education:
            latest_edu = education[0] if education else {}
            school = latest_edu.get('school', 'your university')
            degree = latest_edu.get('degree', 'your degree')
            resume_question_templates.append(
                f"I see you studied {degree} at {school}. How did your education prepare you for this role?"
            )
        
        if not resume_question_templates:
            # Fallback generic resume question
            resume_question_templates.append(
                "Can you walk me through your resume and highlight your most relevant experience for this role?"
            )
        
        # Select a question we haven't asked yet
        available = [q for q in resume_question_templates 
                    if q not in self.used_resume_questions]
        
        if not available:
            return None
        
        selected = random.choice(available)
        self.used_resume_questions.add(selected)
        
        return QuestionContext(
            question=selected,
            question_type="resume",
            phase=InterviewPhase.RESUME_DEEP_DIVE,
            difficulty="medium",
            source="resume_data",
            asked_at=datetime.now()
        )
    
    def _get_technical_question(self) -> Optional[QuestionContext]:
        """Get a technical question from the pool, avoiding previous topics"""
        available = [q for q in self.questions_pool 
                    if q not in self.used_questions]
        
        if not available:
            # If we've used all questions, allow reuse but prefer unused
            available = self.questions_pool
        
        # Filter out questions about topics we've already covered
        filtered = self._filter_by_previous_topics(available)
        if not filtered:
            filtered = available
        
        if not filtered:
            return None
        
        # Adjust difficulty based on performance
        selected = random.choice(filtered)
        self.used_questions.add(selected)
        
        return QuestionContext(
            question=selected,
            question_type="file",
            phase=InterviewPhase.TECHNICAL_QUESTIONS,
            difficulty=self.current_difficulty,
            source="question_file",
            asked_at=datetime.now()
        )
    
    def _filter_by_previous_topics(self, questions: List[str]) -> List[str]:
        """Filter questions to avoid topics covered in previous interviews"""
        if not self.previous_topics:
            return questions
        
        filtered = []
        for q in questions:
            # Simple keyword matching - can be enhanced with NLP
            q_lower = q.lower()
            has_previous_topic = any(topic.lower() in q_lower 
                                   for topic in self.previous_topics)
            if not has_previous_topic:
                filtered.append(q)
        
        return filtered if filtered else questions
    
    def _generate_followup_question(self) -> Optional[QuestionContext]:
        """Generate a follow-up question based on recent answers"""
        if not self.answers_assessed:
            return None
        
        # Find the most recent answer that needs follow-up
        for assessment in reversed(self.answers_assessed):
            if assessment.needs_followup and assessment.quality in [AnswerQuality.FAIR, AnswerQuality.POOR]:
                # Generate follow-up to probe weak area
                followup = self._create_followup_for_weakness(assessment)
                if followup:
                    return followup
        
        # If no weak areas, generate follow-up for good answers to go deeper
        for assessment in reversed(self.answers_assessed):
            if assessment.quality in [AnswerQuality.EXCELLENT, AnswerQuality.GOOD]:
                followup = self._create_followup_for_depth(assessment)
                if followup:
                    return followup
        
        return None
    
    def _create_followup_for_weakness(self, assessment: AnswerAssessment) -> Optional[QuestionContext]:
        """Create a follow-up question to probe a weak area"""
        weaknesses = assessment.weaknesses
        if not weaknesses:
            return None
        
        # Generate follow-up based on weakness
        weakness = weaknesses[0].lower()
        
        # Extract key topic from original question
        question_lower = assessment.question.lower()
        
        followup_templates = [
            f"Let me ask a follow-up: can you elaborate on {weakness}?",
            f"I'd like to understand better: regarding {weakness}, can you provide more details?",
            f"To clarify: what specific challenges have you faced with {weakness}?",
            f"Can you give me an example of how you've worked with {weakness}?",
        ]
        
        selected = random.choice(followup_templates)
        
        return QuestionContext(
            question=selected,
            question_type="followup",
            phase=InterviewPhase.FOLLOW_UP,
            difficulty=self.current_difficulty,
            source="weakness_probe",
            asked_at=datetime.now()
        )
    
    def _create_followup_for_depth(self, assessment: AnswerAssessment) -> Optional[QuestionContext]:
        """Create a follow-up question to go deeper into a good answer"""
        followup_templates = [
            "That's interesting. Can you walk me through a specific example where you applied this?",
            "Great! How would you handle an edge case in this scenario?",
            "Can you elaborate on the implementation details?",
            "What would you do differently if you had to approach this problem again?",
            "Can you give me a real-world scenario where this would be particularly important?",
        ]
        
        selected = random.choice(followup_templates)
        
        return QuestionContext(
            question=selected,
            question_type="followup",
            phase=InterviewPhase.FOLLOW_UP,
            difficulty=self.current_difficulty,
            source="depth_probe",
            asked_at=datetime.now()
        )
    
    def assess_answer(self, question: str, answer: str) -> AnswerAssessment:
        """Assess the quality of an answer (simplified - can use LLM for better assessment)"""
        # This is a simplified version - in production, use LLM to assess
        answer_lower = answer.lower()
        
        # Simple heuristics (replace with LLM-based assessment)
        quality_indicators = {
            "excellent": ["implemented", "designed", "architected", "optimized", "scaled", "built", "created"],
            "good": ["worked with", "familiar", "experience", "used", "applied"],
            "fair": ["heard of", "know about", "read about", "understand"],
            "poor": ["don't know", "not sure", "unfamiliar", "haven't", "no experience"]
        }
        
        score = 50  # Default
        quality = AnswerQuality.FAIR
        
        for q_level, indicators in quality_indicators.items():
            if any(ind in answer_lower for ind in indicators):
                if q_level == "excellent":
                    score = random.uniform(80, 100)
                    quality = AnswerQuality.EXCELLENT
                elif q_level == "good":
                    score = random.uniform(60, 79)
                    quality = AnswerQuality.GOOD
                elif q_level == "fair":
                    score = random.uniform(40, 59)
                    quality = AnswerQuality.FAIR
                else:
                    score = random.uniform(0, 39)
                    quality = AnswerQuality.POOR
                break
        
        # Determine if follow-up is needed
        needs_followup = quality in [AnswerQuality.FAIR, AnswerQuality.POOR] or score < 70
        
        assessment = AnswerAssessment(
            question=question,
            answer=answer,
            quality=quality,
            score=score,
            strengths=[],
            weaknesses=[],
            topics_covered=[],
            needs_followup=needs_followup
        )
        
        self.answers_assessed.append(assessment)
        self._update_difficulty(score)
        
        return assessment
    
    def _update_difficulty(self, score: float):
        """Adjust difficulty based on answer quality"""
        self.difficulty_history.append((self.current_difficulty, score))
        
        # Calculate average score for current difficulty
        recent_scores = [s for d, s in self.difficulty_history[-3:] 
                        if d == self.current_difficulty]
        
        if recent_scores:
            avg_score = sum(recent_scores) / len(recent_scores)
            
            if avg_score >= 80 and self.current_difficulty != "hard":
                self.current_difficulty = "hard"
                logger.info(f"[Adaptive] Increasing difficulty to hard (avg score: {avg_score})")
            elif avg_score < 60 and self.current_difficulty != "easy":
                self.current_difficulty = "easy"
                logger.info(f"[Adaptive] Decreasing difficulty to easy (avg score: {avg_score})")
    
    def record_question_asked(self, question_context: QuestionContext):
        """Record that a question was asked"""
        self.questions_asked.append(question_context)
    
    def get_interview_state(self) -> Dict[str, Any]:
        """Get current interview state"""
        return {
            "phase": self.current_phase.value,
            "questions_asked": len(self.questions_asked),
            "resume_questions": self.resume_questions_asked,
            "technical_questions": self.technical_questions_asked,
            "followup_questions": self.followup_questions_asked,
            "current_difficulty": self.current_difficulty,
            "weak_areas": self.weak_areas,
            "strong_areas": self.strong_areas,
        }

