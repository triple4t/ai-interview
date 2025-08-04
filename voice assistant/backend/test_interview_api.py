#!/usr/bin/env python3
"""
Test script for the interview evaluation API
"""

import requests
import json
from datetime import datetime

# Test data
test_interview_data = {
    "session_id": "test_session_123",
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

def test_interview_evaluation():
    """Test the interview evaluation API"""
    
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Interview Evaluation API")
    print("=" * 50)
    
    try:
        # Test 1: Check if server is running
        print("1. Checking server status...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server is not responding properly")
            return
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:8000")
        print("💡 Start the server with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return
    
    # Test 2: Try to evaluate interview (without auth for now)
    print("\n2. Testing interview evaluation...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/interview/evaluate",
            json=test_interview_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Interview evaluation successful!")
            print(f"📊 Score: {result.get('total_score', 0)}/{result.get('max_score', 100)}")
            print(f"📈 Percentage: {result.get('percentage', 0):.1f}%")
            print(f"📝 Analysis: {result.get('overall_analysis', 'N/A')[:100]}...")
        elif response.status_code == 401:
            print("⚠️  Authentication required - this is expected")
            print("The API is working but requires user authentication")
        else:
            print(f"❌ Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing interview evaluation: {e}")
    
    # Test 3: Check API documentation
    print("\n3. Checking API documentation...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ API documentation available at /docs")
        else:
            print("❌ API documentation not available")
    except Exception as e:
        print(f"❌ Error accessing docs: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test completed!")

if __name__ == "__main__":
    test_interview_evaluation() 