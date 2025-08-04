#!/usr/bin/env python3
"""
Test script to simulate frontend integration with backend
"""

import requests
import json
from datetime import datetime

def test_frontend_integration():
    """Test the complete frontend-backend integration"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Frontend-Backend Integration")
    print("=" * 50)
    
    # Simulate interview data that would come from frontend
    interview_data = {
        "session_id": "session_1234567890_abc123",
        "conversation": [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI interviewer. Let's start with the first question: What does tokenization entail, and why is it critical for LLMs?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user", 
                "content": "Tokenization is the process of breaking down text into smaller units called tokens. These tokens can be words, subwords, or characters. It's critical for LLMs because it allows the model to process and understand text in a structured way. Without tokenization, the model wouldn't be able to handle variable-length text inputs effectively.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Thank you for that detailed explanation. Now, let's move to the second question: How does the attention mechanism work in transformers?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "The attention mechanism allows the model to focus on different parts of the input sequence when processing each token. It computes attention scores between all pairs of tokens, determining how much each token should influence the representation of other tokens. This enables the model to capture long-range dependencies and relationships in the text.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant", 
                "content": "Excellent! For our final question: What is zero-shot learning?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "Zero-shot learning is the ability of a model to perform a task without having been specifically trained on examples of that task. The model leverages its pre-trained knowledge to generalize to new, unseen tasks by understanding the task description or prompt.",
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
            "Tokenization is the process of breaking down text into smaller units called tokens. These tokens can be words, subwords, or characters. It's critical for LLMs because it allows the model to process and understand text in a structured way. Without tokenization, the model wouldn't be able to handle variable-length text inputs effectively.",
            "The attention mechanism allows the model to focus on different parts of the input sequence when processing each token. It computes attention scores between all pairs of tokens, determining how much each token should influence the representation of other tokens. This enables the model to capture long-range dependencies and relationships in the text.",
            "Zero-shot learning is the ability of a model to perform a task without having been specifically trained on examples of that task. The model leverages its pre-trained knowledge to generalize to new, unseen tasks by understanding the task description or prompt."
        ]
    }
    
    try:
        # Test 1: Evaluate interview (simulating frontend request)
        print("1. Testing interview evaluation (frontend simulation)...")
        response = requests.post(
            f"{base_url}/api/v1/interview/evaluate",
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
            print(f"🎯 Overall Analysis: {result.get('overall_analysis', 'N/A')[:100]}...")
            
            # Test 2: Get interview history
            print("\n2. Testing interview history...")
            history_response = requests.get(
                f"{base_url}/api/v1/interview/history",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"History Status Code: {history_response.status_code}")
            if history_response.status_code == 200:
                history = history_response.json()
                print(f"✅ Found {len(history)} interview sessions in history")
            else:
                print(f"❌ History request failed: {history_response.text}")
            
            # Test 3: Get specific session result
            print("\n3. Testing specific session retrieval...")
            session_response = requests.get(
                f"{base_url}/api/v1/interview/{interview_data['session_id']}",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"Session Status Code: {session_response.status_code}")
            if session_response.status_code == 200:
                session_result = session_response.json()
                print(f"✅ Retrieved session: {session_result.get('session_id', 'N/A')}")
            else:
                print(f"❌ Session retrieval failed: {session_response.text}")
                
        else:
            print(f"❌ Interview evaluation failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Frontend-Backend Integration Test Completed!")

if __name__ == "__main__":
    test_frontend_integration() 