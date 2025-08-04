#!/usr/bin/env python3
"""
Comprehensive test for the complete interview evaluation system
"""

import requests
import json
import time

def test_complete_interview_evaluation():
    """Test the complete interview evaluation flow"""
    
    print("🧪 Testing Complete Interview Evaluation System")
    print("=" * 60)
    
    # Test data with proper questions and answers
    test_data = {
        "session_id": f"complete_test_session_{int(time.time())}",
        "conversation": [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI interviewer. Let's begin with the first question. What does tokenization entail, and why is it critical for LLMs?",
                "timestamp": "2025-07-30T15:00:00Z"
            },
            {
                "role": "user", 
                "content": "Tokenization is the process of breaking down text into smaller units called tokens. These tokens can be words, subwords, or characters. It's critical for LLMs because it allows the model to process and understand text in a structured way.",
                "timestamp": "2025-07-30T15:00:30Z"
            },
            {
                "role": "assistant",
                "content": "Thank you for that response. Now for the second question: What is the role of positional encoding in transformers?",
                "timestamp": "2025-07-30T15:01:00Z"
            },
            {
                "role": "user",
                "content": "Positional encoding adds information about the position of tokens in a sequence. Since transformers process all tokens simultaneously, they need this positional information to understand the order and relationships between tokens.",
                "timestamp": "2025-07-30T15:01:30Z"
            },
            {
                "role": "assistant", 
                "content": "Thank you. For the final question: How do you prevent overfitting in large language models?",
                "timestamp": "2025-07-30T15:02:00Z"
            },
            {
                "role": "user",
                "content": "To prevent overfitting in LLMs, you can use techniques like regularization, dropout, early stopping, data augmentation, and cross-validation. You can also use larger datasets and reduce model complexity.",
                "timestamp": "2025-07-30T15:02:30Z"
            },
            {
                "role": "assistant",
                "content": "Thank you so much for your time today. We'll be in touch with the next steps. Have a great day!",
                "timestamp": "2025-07-30T15:03:00Z"
            }
        ],
        "questions": [
            "What does tokenization entail, and why is it critical for LLMs?",
            "What is the role of positional encoding in transformers?",
            "How do you prevent overfitting in large language models?"
        ],
        "answers": [
            "Tokenization is the process of breaking down text into smaller units called tokens. These tokens can be words, subwords, or characters. It's critical for LLMs because it allows the model to process and understand text in a structured way.",
            "Positional encoding adds information about the position of tokens in a sequence. Since transformers process all tokens simultaneously, they need this positional information to understand the order and relationships between tokens.",
            "To prevent overfitting in LLMs, you can use techniques like regularization, dropout, early stopping, data augmentation, and cross-validation. You can also use larger datasets and reduce model complexity."
        ]
    }
    
    print(f"📤 Sending evaluation request to backend...")
    print(f"Session ID: {test_data['session_id']}")
    print(f"Questions: {len(test_data['questions'])}")
    print(f"Answers: {len(test_data['answers'])}")
    
    try:
        # Send evaluation request
        response = requests.post(
            "http://localhost:8000/api/v1/interview/evaluate",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Backend evaluation successful!")
            print(f"Total Score: {result['total_score']}/{result['max_score']}")
            print(f"Percentage: {result['percentage']:.1f}%")
            print(f"Questions Evaluated: {result['questions_evaluated']}")
            print(f"Overall Analysis: {result['overall_analysis'][:150]}...")
            
            print("\n📋 Detailed Feedback:")
            for i, feedback in enumerate(result['detailed_feedback'], 1):
                print(f"Q{i}: Score {feedback['score']}/100")
                print(f"   Feedback: {feedback['feedback'][:100]}...")
                print(f"   Strengths: {feedback['strengths']}")
                print(f"   Weaknesses: {feedback['weaknesses']}")
                print()
            
            print(f"🎯 Overall Strengths: {result['strengths']}")
            print(f"🔧 Areas for Improvement: {result['areas_for_improvement']}")
            print(f"💡 Recommendations: {result['recommendations']}")
            
            # Test that the result is stored in the database
            print("\n🧪 Testing result storage...")
            history_response = requests.get("http://localhost:8000/api/v1/interview/history")
            if history_response.status_code == 200:
                history = history_response.json()
                if len(history) > 0:
                    latest = history[0]
                    print(f"✅ Latest result found in database:")
                    print(f"   Session ID: {latest['session_id']}")
                    print(f"   Score: {latest['total_score']}/{latest['max_score']}")
                    print(f"   Percentage: {latest['percentage']:.1f}%")
                else:
                    print("⚠️ No results found in database")
            else:
                print(f"❌ Failed to fetch history: {history_response.status_code}")
                
        else:
            print(f"❌ Backend evaluation failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing backend evaluation: {e}")

def test_empty_answers():
    """Test with empty answers to simulate 'I don't know' responses"""
    
    print("\n🧪 Testing with Empty Answers")
    print("=" * 40)
    
    test_data = {
        "session_id": f"empty_answers_test_{int(time.time())}",
        "conversation": [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI interviewer. Let's begin with the first question. What does tokenization entail, and why is it critical for LLMs?",
                "timestamp": "2025-07-30T15:00:00Z"
            },
            {
                "role": "user", 
                "content": "I don't know",
                "timestamp": "2025-07-30T15:00:30Z"
            },
            {
                "role": "assistant",
                "content": "Thank you for that response. Now for the second question: What is the role of positional encoding in transformers?",
                "timestamp": "2025-07-30T15:01:00Z"
            },
            {
                "role": "user",
                "content": "I don't know",
                "timestamp": "2025-07-30T15:01:30Z"
            },
            {
                "role": "assistant", 
                "content": "Thank you. For the final question: How do you prevent overfitting in large language models?",
                "timestamp": "2025-07-30T15:02:00Z"
            },
            {
                "role": "user",
                "content": "I don't know",
                "timestamp": "2025-07-30T15:02:30Z"
            },
            {
                "role": "assistant",
                "content": "Thank you so much for your time today. We'll be in touch with the next steps. Have a great day!",
                "timestamp": "2025-07-30T15:03:00Z"
            }
        ],
        "questions": [
            "What does tokenization entail, and why is it critical for LLMs?",
            "What is the role of positional encoding in transformers?",
            "How do you prevent overfitting in large language models?"
        ],
        "answers": [
            "I don't know",
            "I don't know", 
            "I don't know"
        ]
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/interview/evaluate",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Empty answers evaluation successful!")
            print(f"Total Score: {result['total_score']}/{result['max_score']}")
            print(f"Percentage: {result['percentage']:.1f}%")
            print(f"Overall Analysis: {result['overall_analysis'][:100]}...")
        else:
            print(f"❌ Empty answers evaluation failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing empty answers: {e}")

if __name__ == "__main__":
    print("🚀 Starting Complete Interview Evaluation Tests")
    print("=" * 60)
    
    # Test with good answers
    test_complete_interview_evaluation()
    
    # Test with empty answers
    test_empty_answers()
    
    print("\n✅ All tests completed!") 