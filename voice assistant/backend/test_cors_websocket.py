#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging

# Enable logging
logging.basicConfig(level=logging.DEBUG)

async def test_cors_websocket():
    """Test WebSocket connection with CORS headers"""
    try:
        uri = "ws://localhost:8000/api/v1/face-detection/ws/test_cors_client"
        print(f"🔌 Testing WebSocket connection to {uri}")
        
        # Add custom headers to simulate browser request
        extra_headers = {
            'Origin': 'http://localhost:3000',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        async with websockets.connect(uri, extra_headers=extra_headers) as websocket:
            print("✅ WebSocket connection successful with CORS headers!")
            
            # Wait for a few messages
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📊 Received message {i+1}: {data.get('type', 'unknown')}")
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                    
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused. Server might not be running.")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Invalid status code: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_cors_websocket()) 