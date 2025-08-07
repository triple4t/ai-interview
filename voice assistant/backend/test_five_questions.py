#!/usr/bin/env python3
"""
Test the interview system with exactly 5 questions
"""

import requests
import json
from datetime import datetime

def test_five_questions():
    """Test the interview system with exactly 5 questions"""
    
    print("🧪 Testing Interview System with Exactly 5 Questions")
    print("=" * 60)
    
    # Simulate interview data with exactly 5 questions
    interview_data = {
        "session_id": f"session_{int(datetime.now().timestamp())}_test_5q",
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
                "content": "How does the attention mechanism work in transformers?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "The attention mechanism allows the model to focus on different parts of the input sequence when processing each token. It computes attention scores between all pairs of tokens, determining how much each token should influence the representation of other tokens.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Why is cross-entropy loss used in language modeling?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "Cross-entropy loss is used because it measures the difference between the predicted probability distribution and the true distribution. It's particularly effective for classification tasks like next-token prediction in language models.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "What is the role of positional encoding in transformers?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "Positional encoding provides information about the position of tokens in a sequence since transformers don't have inherent sequential processing like RNNs. It allows the model to understand the order and relationships between tokens.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "How do you prevent overfitting in large language models?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "Overfitting can be prevented through techniques like dropout, regularization, early stopping, data augmentation, and using validation sets to monitor performance. Cross-validation and reducing model complexity can also help.",
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
            "Why is cross-entropy loss used in language modeling?",
            "What is the role of positional encoding in transformers?",
            "How do you prevent overfitting in large language models?"
        ],
        "answers": [
            "Tokenization is the process of breaking down text into smaller units called tokens. These tokens can be words, subwords, or characters. It's critical for LLMs because it allows the model to process and understand text in a structured way.",
            "The attention mechanism allows the model to focus on different parts of the input sequence when processing each token. It computes attention scores between all pairs of tokens, determining how much each token should influence the representation of other tokens.",
            "Cross-entropy loss is used because it measures the difference between the predicted probability distribution and the true distribution. It's particularly effective for classification tasks like next-token prediction in language models.",
            "Positional encoding provides information about the position of tokens in a sequence since transformers don't have inherent sequential processing like RNNs. It allows the model to understand the order and relationships between tokens.",
            "Overfitting can be prevented through techniques like dropout, regularization, early stopping, data augmentation, and using validation sets to monitor performance. Cross-validation and reducing model complexity can also help."
        ]
    }
    
    print(f"📝 Questions provided: {len(interview_data['questions'])}")
    print(f"📝 Answers provided: {len(interview_data['answers'])}")
    print(f"📝 Conversation messages: {len(interview_data['conversation'])}")
    
    try:
        # Test interview evaluation
        print("\n1. Testing interview evaluation with exactly 5 questions...")
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
            
            # Verify we have exactly 5 questions evaluated
            if len(detailed_feedback) == 5:
                print("✅ Perfect! Exactly 5 questions were evaluated.")
            else:
                print(f"⚠️ Warning: Expected 5 questions, got {len(detailed_feedback)}")
                
            # Test 2: Get interview history
            print("\n2. Testing interview history...")
            history_response = requests.get(
                "http://localhost:8000/api/v1/interview/history",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"History Status Code: {history_response.status_code}")
            if history_response.status_code == 200:
                history = history_response.json()
                print(f"✅ Found {len(history)} interview sessions in history")
                
                # Check if our 5-question session is in the history
                our_session = next((s for s in history if s.get('session_id') == interview_data['session_id']), None)
                if our_session:
                    print(f"✅ Found our 5-question session in history")
                    print(f"   Questions evaluated: {our_session.get('questions_evaluated', 0)}")
                else:
                    print("⚠️ Our session not found in history yet")
            else:
                print(f"❌ History request failed: {history_response.text}")
                
        else:
            print(f"❌ Interview evaluation failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")

    print("\n🎯 5-Question Test completed!")

if __name__ == "__main__":
    test_five_questions()