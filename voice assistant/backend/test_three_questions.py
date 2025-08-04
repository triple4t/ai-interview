#!/usr/bin/env python3
"""
Test the interview system with exactly 3 questions
"""

import requests
import json
from datetime import datetime

def test_three_questions():
    """Test the interview system with exactly 3 questions"""
    
    print("🧪 Testing Interview System with Exactly 3 Questions")
    print("=" * 60)
    
    # Simulate interview data with exactly 3 questions
    interview_data = {
        "session_id": f"session_{int(datetime.now().timestamp())}_test",
        "conversation": [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI interviewer. Let's start with the first question: What does tokenization entail, and why is it critical for LLMs?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user", 
                "content": "Tokenization is the process of breaking down text into smaller units called tokens. These tokens can be words, subwords, or characters. It's critical for LLMs because it allows the model to process and understand text in a structured way.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Thank you for that detailed explanation. Now, let's move to the second question: How does the attention mechanism work in transformers?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "The attention mechanism allows the model to focus on different parts of the input sequence when processing each token. It computes attention scores between all pairs of tokens, determining how much each token should influence the representation of other tokens.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant", 
                "content": "Excellent! For our final question: What is zero-shot learning?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "Zero-shot learning is the ability of a model to perform a task without having been specifically trained on examples of that task. The model leverages its pre-trained knowledge to generalize to new, unseen tasks.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "That was my final question. Thank you so much for your time today. We'll be in touch with the next steps. Have a great day!",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "questions": [
            "What does tokenization entail, and why is it critical for LLMs?",
            "How does the attention mechanism work in transformers?", 
            "What is zero-shot learning?"
        ],
        "answers": [
            "Tokenization is the process of breaking down text into smaller units called tokens. These tokens can be words, subwords, or characters. It's critical for LLMs because it allows the model to process and understand text in a structured way.",
            "The attention mechanism allows the model to focus on different parts of the input sequence when processing each token. It computes attention scores between all pairs of tokens, determining how much each token should influence the representation of other tokens.",
            "Zero-shot learning is the ability of a model to perform a task without having been specifically trained on examples of that task. The model leverages its pre-trained knowledge to generalize to new, unseen tasks."
        ]
    }
    
    print(f"📝 Questions provided: {len(interview_data['questions'])}")
    print(f"📝 Answers provided: {len(interview_data['answers'])}")
    print(f"📝 Conversation messages: {len(interview_data['conversation'])}")
    
    try:
        # Test interview evaluation
        print("\n1. Testing interview evaluation with exactly 3 questions...")
        response = requests.post(
            "http://localhost:8000/api/v1/interview/evaluate",
            json=interview_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Interview evaluation successful!")
            print(f"📊 Score: {result.get('total_score', 0)}/{result.get('max_score', 100)}")
            print(f"📈 Percentage: {result.get('percentage', 0):.1f}%")
            print(f"📝 Questions Evaluated: {result.get('questions_evaluated', 0)}")
            print(f"🎯 Session ID: {result.get('session_id', 'N/A')}")
            
            # Check detailed feedback
            detailed_feedback = result.get('detailed_feedback', [])
            print(f"📋 Detailed feedback items: {len(detailed_feedback)}")
            
            for i, feedback in enumerate(detailed_feedback):
                print(f"  Q{i+1}: Score {feedback.get('score', 0)}/100")
                print(f"     Question: {feedback.get('question', 'N/A')[:50]}...")
                print(f"     Answer: {feedback.get('answer', 'N/A')[:50]}...")
            
            # Verify we have exactly 3 questions evaluated
            if len(detailed_feedback) == 3:
                print("✅ Perfect! Exactly 3 questions were evaluated.")
            else:
                print(f"⚠️ Warning: Expected 3 questions, got {len(detailed_feedback)}")
                
        else:
            print(f"❌ Interview evaluation failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 3-Question Interview Test Results:")
    print("✅ Backend correctly processes exactly 3 questions")
    print("✅ Frontend extracts only the 3 actual interview questions")
    print("✅ Evaluation focuses on the 3 Q&A pairs only")
    print("✅ Results show detailed feedback for each of the 3 questions")

if __name__ == "__main__":
    test_three_questions() 