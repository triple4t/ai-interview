#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_websocket():
    try:
        uri = "ws://localhost:8000/api/v1/face-detection/ws/test_client"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection successful!")
            
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
        print("❌ Connection refused. Server might not be running or WebSocket not supported.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 