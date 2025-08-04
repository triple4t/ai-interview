#!/usr/bin/env python3
"""
Test script to simulate interview conversation and test question extraction
"""

# Simulate the conversation messages that would be sent from the frontend
test_conversation = [
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
]

def test_question_extraction():
    """Test the question extraction logic"""
    
    print("🧪 Testing Question Extraction Logic")
    print("=" * 50)
    
    # Simulate the frontend extraction logic
    questions = []
    answers = []
    
    for i in range(len(test_conversation)):
        msg = test_conversation[i]
        if msg["role"] == "assistant":
            message_content = msg["content"].lower()
            
            print(f"\n🔍 Analyzing message {i}: {msg['content'][:100]}...")
            
            # Check if this message contains an actual question
            has_question_mark = "?" in msg["content"]
            contains_question_words = any(word in message_content for word in ["what", "how", "why", "when", "where", "which", "who"])
            is_greeting = any(word in message_content for word in ["hello", "greet", "welcome", "hi"]) and not has_question_mark
            is_closing = any(phrase in message_content for phrase in ["thank you so much", "have a great day", "we'll be in touch"]) and not has_question_mark
            is_instruction = any(phrase in message_content for phrase in ["say hello", "start the interview"]) and not has_question_mark
            
            print(f"  - Has question mark: {has_question_mark}")
            print(f"  - Contains question words: {contains_question_words}")
            print(f"  - Is greeting: {is_greeting}")
            print(f"  - Is closing: {is_closing}")
            print(f"  - Is instruction: {is_instruction}")
            
            # Count as a question if it has a question mark or contains question words, and is not a pure greeting/closing/instruction
            # Also check if it contains "question:" which indicates it's an interview question
            is_interview_question = (has_question_mark or contains_question_words or "question:" in message_content) and not is_greeting and not is_closing and not is_instruction
            
            print(f"  - Is interview question: {is_interview_question}")
            
            if is_interview_question:
                question = msg["content"]
                print(f"🎯 Found question {len(questions) + 1}: {question}")
                questions.append(question)
                
                # Look for the next user message as the answer
                for j in range(i + 1, len(test_conversation)):
                    next_msg = test_conversation[j]
                    if next_msg["role"] == "user":
                        answer = next_msg["content"]
                        print(f"💬 Found answer: {answer}")
                        answers.append(answer)
                        break
            else:
                print(f"⏭️ Skipping message: {message_content[:50]}... - not a question")
    
    print(f"\n📝 Final Results:")
    print(f"Questions extracted: {len(questions)}")
    print(f"Answers extracted: {len(answers)}")
    
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"\nQ{i}: {q}")
        print(f"A{i}: {a}")
    
    return questions, answers

def test_backend_evaluation(questions, answers):
    """Test the backend evaluation with the extracted data"""
    
    print("\n🧪 Testing Backend Evaluation")
    print("=" * 50)
    
    import requests
    import json
    
    # Prepare the evaluation request
    evaluation_data = {
        "session_id": f"test_session_{int(time.time())}",
        "conversation": test_conversation,
        "questions": questions,
        "answers": answers
    }
    
    print(f"📤 Sending to backend:")
    print(f"Session ID: {evaluation_data['session_id']}")
    print(f"Questions: {questions}")
    print(f"Answers: {answers}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/interview/evaluate",
            json=evaluation_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Backend evaluation successful!")
            print(f"Total Score: {result['total_score']}/{result['max_score']}")
            print(f"Percentage: {result['percentage']:.1f}%")
            print(f"Overall Analysis: {result['overall_analysis'][:100]}...")
            
            print("\n📋 Detailed Feedback:")
            for i, feedback in enumerate(result['detailed_feedback'], 1):
                print(f"Q{i}: Score {feedback['score']}/100 - {feedback['feedback'][:80]}...")
                
        else:
            print(f"❌ Backend evaluation failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing backend evaluation: {e}")

if __name__ == "__main__":
    import time
    
    print("🚀 Starting Interview Extraction Test")
    print("=" * 60)
    
    # Test question extraction
    questions, answers = test_question_extraction()
    
    # Test backend evaluation
    test_backend_evaluation(questions, answers)
    
    print("\n✅ Test completed!") 