#!/usr/bin/env python3
"""
Test script to verify transcript functionality
"""

import requests
import json
from datetime import datetime

def test_transcript_functionality():
    """Test the transcript functionality by sending a mock interview session"""
    
    # Mock interview data
    session_data = {
        "session_id": "test_session_123",
        "conversation": [
            {
                "role": "assistant",
                "content": "Hello! Welcome to your technical interview. Let's start with the first question.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user", 
                "content": "Hello! I'm ready to begin.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "How does the attention mechanism work in transformers?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "The attention mechanism allows the model to focus on different parts of the input sequence when processing each token. It computes attention scores between query, key, and value vectors.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant", 
                "content": "Great! Now for the second question: What is the difference between supervised and unsupervised learning?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Excellent! Final question: Explain the concept of overfitting in machine learning.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "Overfitting occurs when a model learns the training data too well, including noise, and performs poorly on new data.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Thank you for your responses! The interview is now complete.",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "questions": [
            "How does the attention mechanism work in transformers?",
            "What is the difference between supervised and unsupervised learning?", 
            "Explain the concept of overfitting in machine learning."
        ],
        "answers": [
            "The attention mechanism allows the model to focus on different parts of the input sequence when processing each token. It computes attention scores between query, key, and value vectors.",
            "Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data.",
            "Overfitting occurs when a model learns the training data too well, including noise, and performs poorly on new data."
        ]
    }
    
    try:
        # Send request to backend
        response = requests.post(
            "http://localhost:8000/api/v1/interview/evaluate",
            json=session_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Interview evaluation successful!")
            print(f"Session ID: {result['session_id']}")
            print(f"Score: {result['total_score']}/{result['max_score']} ({result['percentage']:.1f}%)")
            print(f"Questions evaluated: {result['questions_evaluated']}")
            
            # Check if transcript is included
            if 'transcript' in result and result['transcript']:
                print(f"✅ Transcript included with {len(result['transcript'])} messages")
                print("Transcript preview:")
                for i, msg in enumerate(result['transcript'][:3]):  # Show first 3 messages
                    print(f"  {msg['role']}: {msg['content'][:50]}...")
            else:
                print("❌ No transcript found in response")
                
            return result
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server. Make sure it's running on localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Testing transcript functionality...")
    result = test_transcript_functionality()
    
    if result:
        print("\n📋 Full response structure:")
        print(json.dumps(result, indent=2, default=str)) 