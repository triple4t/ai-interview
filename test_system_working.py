#!/usr/bin/env python3
"""
Simple test to verify the system is working correctly
"""

import requests
import json
import time

def test_system():
    """Test that the system is working correctly"""
    
    print("🧪 Testing System Functionality")
    print("=" * 40)
    
    # Test 1: Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Test 2: Send a simple evaluation request
    test_data = {
        "session_id": f"test_system_{int(time.time())}",
        "conversation": [
            {
                "role": "assistant",
                "content": "What does tokenization entail, and why is it critical for LLMs?",
                "timestamp": "2025-07-30T15:00:00Z"
            },
            {
                "role": "user", 
                "content": "I don't know",
                "timestamp": "2025-07-30T15:00:30Z"
            }
        ],
        "questions": [
            "What does tokenization entail, and why is it critical for LLMs?"
        ],
        "answers": [
            "I don't know"
        ]
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/interview/evaluate",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Evaluation API working")
            print(f"   Score: {result['total_score']}/{result['max_score']}")
            print(f"   Percentage: {result['percentage']:.1f}%")
            
            # Test 3: Check if result is stored
            history_response = requests.get("http://localhost:8000/api/v1/interview/history")
            if history_response.status_code == 200:
                history = history_response.json()
                if len(history) > 0:
                    latest = history[0]
                    print("✅ History API working")
                    print(f"   Latest session: {latest['session_id']}")
                    print(f"   Latest score: {latest['total_score']}/{latest['max_score']}")
                else:
                    print("⚠️ No history found")
            else:
                print(f"❌ History API failed: {history_response.status_code}")
                
        else:
            print(f"❌ Evaluation API failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing system: {e}")

if __name__ == "__main__":
    print("🚀 Testing System Functionality")
    print("=" * 60)
    
    test_system()
    
    print("\n✅ Test completed!") 