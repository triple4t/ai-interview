from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import cv2
import base64
import numpy as np
import json
import asyncio
from typing import Dict, Any
import logging

# Simple face detection using OpenCV
class SimpleFaceDetector:
    def __init__(self):
        # Use OpenCV's built-in face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
    def detect_faces(self, frame):
        """Detect faces in the frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return faces
    
    def detect_eyes(self, frame, face_roi):
        """Detect eyes within a face region"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        x, y, w, h = face_roi
        roi_gray = gray[y:y+h, x:x+w]
        eyes = self.eye_cascade.detectMultiScale(roi_gray)
        return eyes
    
    def analyze_emotion_simple(self, frame, face_roi):
        """Simple emotion analysis based on facial features"""
        x, y, w, h = face_roi
        face_region = frame[y:y+h, x:x+w]
        
        # Convert to grayscale for analysis
        gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        
        # Simple analysis based on brightness and contrast
        brightness = np.mean(gray_face)
        contrast = np.std(gray_face)
        
        # Very basic emotion estimation
        if brightness > 120:
            emotion = "happy"
        elif brightness < 80:
            emotion = "sad"
        else:
            emotion = "neutral"
            
        return emotion, brightness / 255.0, contrast / 255.0
    
    def process_frame(self, frame):
        """Process a frame and return analysis data"""
        # Detect faces
        faces = self.detect_faces(frame)
        
        analysis_data = {
            "face_detected": len(faces) > 0,
            "face_count": len(faces),
            "confidence": 0.0,
            "attention_score": 0.0,
            "engagement_level": "low"
        }
        
        if len(faces) > 0:
            # Get the largest face (assumed to be the main subject)
            largest_face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = largest_face
            
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Detect eyes
            eyes = self.detect_eyes(frame, largest_face)
            eye_state = "open" if len(eyes) >= 2 else "closed" if len(eyes) == 0 else "blinking"
            
            # Analyze emotion
            emotion, brightness, contrast = self.analyze_emotion_simple(frame, largest_face)
            
            # Calculate confidence based on face size and eye detection
            face_area = w * h
            frame_area = frame.shape[0] * frame.shape[1]
            face_ratio = face_area / frame_area
            confidence = min(face_ratio * 10, 0.95)  # Scale confidence
            
            # Calculate attention score based on eye detection
            attention_score = min(len(eyes) / 2.0, 1.0)
            
            # Determine engagement level
            if attention_score > 0.8 and confidence > 0.7:
                engagement_level = "high"
            elif attention_score > 0.5 and confidence > 0.5:
                engagement_level = "medium"
            else:
                engagement_level = "low"
            
            # Update analysis data
            analysis_data.update({
                "emotion": emotion,
                "eye_state": eye_state,
                "confidence": confidence,
                "attention_score": attention_score,
                "engagement_level": engagement_level,
                "face_area_ratio": face_ratio,
                "eyes_detected": len(eyes)
            })
            
            # Add recommendations
            recommendations = []
            if engagement_level == "low":
                recommendations.append("Try to look directly at the camera")
            if eye_state == "closed":
                recommendations.append("Keep your eyes open and focused")
            if emotion == "sad":
                recommendations.append("Try to maintain a positive expression")
            if face_ratio < 0.1:
                recommendations.append("Move closer to the camera")
                
            analysis_data["recommendations"] = recommendations
            
            # Draw eye rectangles
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(frame, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (0, 255, 0), 2)
        
        return frame, analysis_data

# Global face detection manager
face_detector = SimpleFaceDetector()

router = APIRouter(prefix="/face-detection", tags=["face-detection"])

class FaceDetectionManager:
    def __init__(self):
        self.camera = None
        self.is_streaming = False
        self.connections = {}
        self.camera_started = False  # Track if camera has been explicitly started
    
    async def start_camera(self):
        """Initialize and start the camera"""
        if self.camera is None or not self.camera.isOpened():
            print(f"🎥 Attempting to open camera...")
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print(f"❌ Failed to open camera")
                raise Exception("Could not open camera")
            print(f"✅ Camera opened successfully")
            self.camera_started = True
        return True
    
    async def stop_camera(self):
        """Stop and release the camera"""
        if self.camera and self.camera.isOpened():
            self.camera.release()
            self.camera = None
        self.is_streaming = False
        self.camera_started = False
    
    async def process_frame(self, frame):
        """Process a single frame and return analysis data"""
        try:
            annotated_frame, analysis_data = face_detector.process_frame(frame)
            return annotated_frame, analysis_data
        except Exception as e:
            logging.error(f"Error processing frame: {e}")
            return frame, {"error": str(e)}
    
    async def stream_video(self, websocket: WebSocket, client_id: str):
        """Stream video frames to the client"""
        try:
            print(f"🎥 Starting video stream for client {client_id}")
            
            # Don't start camera immediately - wait for explicit start command
            self.is_streaming = True
            self.connections[client_id] = websocket
            print(f"✅ WebSocket connection established for client {client_id}")
            
            # Send initial connection success message
            await websocket.send_json({
                "type": "connected",
                "data": {
                    "message": "Face detection service connected successfully",
                    "camera_started": self.camera_started
                }
            })
            
            while self.is_streaming and client_id in self.connections:
                if self.camera and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret:
                        # Process the frame
                        annotated_frame, analysis_data = await self.process_frame(frame)
                        
                        # Encode frame to base64
                        _, buffer = cv2.imencode('.jpg', annotated_frame)
                        frame_bytes = base64.b64encode(buffer).decode('utf-8')
                        
                        # Send frame and analysis data
                        try:
                            await websocket.send_json({
                                "type": "video_frame",
                                "data": {
                                    "image": frame_bytes,
                                    "analysis": analysis_data
                                }
                            })
                        except Exception as e:
                            print(f"❌ Error sending frame to client {client_id}: {e}")
                            break
                        
                        # Small delay to control frame rate
                        await asyncio.sleep(0.033)  # ~30 FPS
                    else:
                        print(f"⚠️ Failed to read frame from camera for client {client_id}")
                        # Camera error, try to restart
                        await self.stop_camera()
                        await asyncio.sleep(1)
                        await self.start_camera()
                else:
                    # Only log camera not available if we're supposed to be streaming
                    if self.camera_started:
                        print(f"⚠️ Camera not available for client {client_id}")
                    # Don't spam logs when camera hasn't been started yet
                    await asyncio.sleep(1)
                    
        except WebSocketDisconnect:
            logging.info(f"Client {client_id} disconnected")
        except Exception as e:
            logging.error(f"Error in video stream: {e}")
        finally:
            if client_id in self.connections:
                del self.connections[client_id]
            if not self.connections:
                await self.stop_camera()

# Global face detection manager
face_manager = FaceDetectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for face detection streaming"""
    try:
        print(f"🔌 WebSocket connection attempt from client {client_id}")
        await websocket.accept()
        print(f"✅ Client {client_id} connected to face detection")
        logging.info(f"Client {client_id} connected to face detection")
        
        # Start video streaming (but don't start camera yet)
        await face_manager.stream_video(websocket, client_id)
    except WebSocketDisconnect:
        print(f"🔌 Client {client_id} disconnected")
        logging.info(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"❌ Error with client {client_id}: {e}")
        logging.error(f"Error with client {client_id}: {e}")
        try:
            await websocket.close()
        except:
            pass

@router.post("/start-camera/{client_id}")
async def start_camera_for_client(client_id: str):
    """Start camera for a specific client"""
    try:
        if client_id in face_manager.connections:
            print(f"🎥 Starting camera for client {client_id}")
            await face_manager.start_camera()
            return {"status": "success", "message": "Camera started successfully"}
        else:
            return {"status": "error", "message": "Client not connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/stop-camera/{client_id}")
async def stop_camera_for_client(client_id: str):
    """Stop camera for a specific client"""
    try:
        if client_id in face_manager.connections:
            print(f"🛑 Stopping camera for client {client_id}")
            await face_manager.stop_camera()
            return {"status": "success", "message": "Camera stopped successfully"}
        else:
            return {"status": "error", "message": "Client not connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/start")
async def start_face_detection():
    """Start face detection service"""
    try:
        await face_manager.start_camera()
        return {"status": "success", "message": "Face detection started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/stop")
async def stop_face_detection():
    """Stop face detection service"""
    try:
        await face_manager.stop_camera()
        return {"status": "success", "message": "Face detection stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/status")
async def get_face_detection_status():
    """Get current face detection status"""
    return {
        "is_streaming": face_manager.is_streaming,
        "camera_available": face_manager.camera is not None and face_manager.camera.isOpened(),
        "camera_started": face_manager.camera_started,
        "active_connections": len(face_manager.connections)
    } 