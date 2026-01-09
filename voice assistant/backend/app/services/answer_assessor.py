from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
import logging
import json

logger = logging.getLogger(__name__)


class AnswerAssessor:
    """Assesses answer quality using LLM"""
    
    def __init__(self):
        self.model = None
        if os.getenv("OPENAI_API_KEY"):
            try:
                self.model = ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=os.getenv("OPENAI_API_KEY"),
                    temperature=0.3
                )
            except Exception as e:
                logger.error(f"Error initializing answer assessor: {e}")
    
    def assess_answer(
        self, 
        question: str, 
        answer: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Assess answer quality and extract insights"""
        if not self.model:
            # Fallback to simple assessment
            return self._simple_assess(answer)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert technical interviewer assessing candidate answers.

Analyze the answer and provide:
1. Quality score (0-100)
2. Quality level (excellent/good/fair/poor)
3. Strengths (list)
4. Weaknesses (list)
5. Topics covered (list)
6. Whether follow-up is needed (boolean)

Be strict but fair. Excellent answers (80-100) show deep understanding and experience.
Good answers (60-79) show solid understanding.
Fair answers (40-59) show basic knowledge.
Poor answers (0-39) show lack of knowledge or understanding.

Return JSON format:
{
    "score": <0-100>,
    "quality": "<excellent|good|fair|poor>",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "topics_covered": ["topic1", "topic2"],
    "needs_followup": <true|false>
}"""),
            ("user", f"""Question: {question}

Answer: {answer}

Context: {context or 'None'}

Assess this answer and return JSON.""")
        ])
        
        try:
            response = self.model.invoke(prompt.format_messages())
            content = response.content.strip()
            
            # Try to parse JSON (handle markdown code blocks)
            if content.startswith("```"):
                # Extract JSON from code block
                lines = content.split("\n")
                json_lines = [l for l in lines if not l.strip().startswith("```")]
                content = "\n".join(json_lines)
            
            result = json.loads(content)
            
            # Validate and set defaults
            if "score" not in result:
                result["score"] = 50
            if "quality" not in result:
                result["quality"] = "fair"
            if "strengths" not in result:
                result["strengths"] = []
            if "weaknesses" not in result:
                result["weaknesses"] = []
            if "topics_covered" not in result:
                result["topics_covered"] = []
            if "needs_followup" not in result:
                result["needs_followup"] = result.get("score", 50) < 70
            
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from answer assessor: {e}, response: {response.content[:200]}")
            return self._simple_assess(answer)
        except Exception as e:
            logger.error(f"Error assessing answer: {e}")
            return self._simple_assess(answer)
    
    def _simple_assess(self, answer: str) -> Dict[str, Any]:
        """Simple fallback assessment"""
        answer_lower = answer.lower()
        length = len(answer.split())
        
        if length < 10:
            return {
                "score": 20,
                "quality": "poor",
                "strengths": [],
                "weaknesses": ["Answer too brief"],
                "topics_covered": [],
                "needs_followup": True
            }
        elif length < 30:
            return {
                "score": 50,
                "quality": "fair",
                "strengths": [],
                "weaknesses": ["Could be more detailed"],
                "topics_covered": [],
                "needs_followup": True
            }
        else:
            return {
                "score": 70,
                "quality": "good",
                "strengths": ["Detailed answer"],
                "weaknesses": [],
                "topics_covered": [],
                "needs_followup": False
            }

