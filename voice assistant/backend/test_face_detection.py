#!/usr/bin/env python3
"""
Test script for face detection integration
"""

import asyncio
import websockets
import json
import base64
import cv2
import numpy as np
from datetime import datetime

async def test_face_detection_websocket():
    """Test the face detection WebSocket endpoint"""
    
    # Test WebSocket connection
    uri = "ws://localhost:8000/api/v1/face-detection/ws/test_client"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to face detection WebSocket")
            
            # Wait for messages
            message_count = 0
            start_time = datetime.now()
            
            while message_count < 10:  # Test for 10 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "video_frame":
                        message_count += 1
                        analysis = data.get("data", {}).get("analysis", {})
                        
                        print(f"📊 Message {message_count}:")
                        print(f"   - Face detected: {analysis.get('face_detected', 'N/A')}")
                        print(f"   - Emotion: {analysis.get('emotion', 'N/A')}")
                        print(f"   - Eye state: {analysis.get('eye_state', 'N/A')}")
                        print(f"   - Confidence: {analysis.get('confidence', 'N/A')}")
                        print(f"   - Image data length: {len(data.get('data', {}).get('image', ''))}")
                        print()
                        
                        # Check if we have image data
                        if data.get("data", {}).get("image"):
                            print("✅ Image data received successfully")
                        else:
                            print("⚠️  No image data received")
                            
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    break
            
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"⏱️  Test completed in {elapsed:.2f} seconds")
            print(f"📈 Received {message_count} messages")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused. Make sure the FastAPI server is running on port 8000")
    except Exception as e:
        print(f"❌ Error connecting to WebSocket: {e}")

async def test_face_detection_api():
    """Test the face detection REST API endpoints"""
    
    import httpx
    
    base_url = "http://localhost:8000/api/v1/face-detection"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test status endpoint
            response = await client.get(f"{base_url}/status")
            if response.status_code == 200:
                status_data = response.json()
                print("✅ Status endpoint working:")
                print(f"   - Streaming: {status_data.get('is_streaming', 'N/A')}")
                print(f"   - Camera available: {status_data.get('camera_available', 'N/A')}")
                print(f"   - Active connections: {status_data.get('active_connections', 'N/A')}")
            else:
                print(f"❌ Status endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing API endpoints: {e}")

async def main():
    """Run all tests"""
    print("🧪 Starting face detection integration tests...")
    print("=" * 50)
    
    print("\n1️⃣ Testing REST API endpoints...")
    await test_face_detection_api()
    
    print("\n2️⃣ Testing WebSocket connection...")
    await test_face_detection_websocket()
    
    print("\n" + "=" * 50)
    print("✅ Face detection integration tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 