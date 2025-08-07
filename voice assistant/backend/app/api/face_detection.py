from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import cv2
import base64
import numpy as np
import json
import asyncio
from typing import Dict, Any, List
import logging
import mediapipe as mp
from scipy.spatial import distance as dist
import requests
import time
from app.services.voice_analysis import voice_analysis_service

# Enhanced face detection using MediaPipe and OpenCV
class EnhancedFaceDetector:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize face detection and mesh
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=10,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Use OpenCV's built-in face detection as backup
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Head pose estimation points
        self.FACE_3D_POINTS = np.array([
            [0.0, 0.0, 0.0],           # Nose tip
            [0.0, -330.0, -65.0],      # Chin
            [-225.0, 170.0, -135.0],   # Left eye left corner
            [225.0, 170.0, -135.0],    # Right eye right corner
            [-150.0, -150.0, -125.0],  # Left mouth corner
            [150.0, -150.0, -125.0]    # Right mouth corner
        ])
        
        # Voice analysis state
        self.voice_analysis_state = {
            "speaking": False,
            "confidence": 0.0,
            "nervousness": 0.0,
            "speech_patterns": []
        }
        
        # Screen sharing detection
        self.screen_sharing_detected = False
        self.last_activity_time = time.time()
        
    def detect_faces_mediapipe(self, frame):
        """Detect faces using MediaPipe"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)
        return results.detections if results.detections else []
    
    def detect_faces_opencv(self, frame):
        """Detect faces using OpenCV as backup"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return faces
    
    def analyze_head_pose(self, frame, face_landmarks):
        """Analyze head pose using MediaPipe landmarks"""
        if not face_landmarks:
            return {"looking_at_screen": False, "head_pose": "unknown"}
        
        try:
            # Get key facial landmarks
            landmarks = face_landmarks.landmark
            
            # Get image dimensions
            h, w = frame.shape[:2]
            
            # Check if we have enough landmarks
            if len(landmarks) < 468:  # MediaPipe face mesh has 468 landmarks
                return {"looking_at_screen": False, "head_pose": "unknown"}
            
            # Extract key points for head pose estimation with bounds checking
            nose_tip = [float(landmarks[1].x * w), float(landmarks[1].y * h)] if len(landmarks) > 1 else [float(w/2), float(h/2)]
            left_eye = [float(landmarks[33].x * w), float(landmarks[33].y * h)] if len(landmarks) > 33 else [float(w/3), float(h/2)]
            right_eye = [float(landmarks[263].x * w), float(landmarks[263].y * h)] if len(landmarks) > 263 else [float(2*w/3), float(h/2)]
            
            # Calculate eye center
            eye_center = [(left_eye[0] + right_eye[0]) / 2, (left_eye[1] + right_eye[1]) / 2]
            
            # Calculate gaze direction (simplified)
            screen_center = [w / 2, h / 2]
            gaze_vector = [eye_center[0] - screen_center[0], eye_center[1] - screen_center[1]]
            gaze_distance = float(np.sqrt(gaze_vector[0]**2 + gaze_vector[1]**2))
            
            # Determine if looking at screen
            looking_at_screen = bool(gaze_distance < (w * 0.3))  # Within 30% of screen center
            
            # Head pose estimation
            eye_distance = float(dist.euclidean(left_eye, right_eye))
            head_pose = "center"
            
            if left_eye[0] < (w * 0.4):
                head_pose = "left"
            elif right_eye[0] > (w * 0.6):
                head_pose = "right"
            elif eye_center[1] < (h * 0.4):
                head_pose = "up"
            elif eye_center[1] > (h * 0.6):
                head_pose = "down"
            
            return {
                "looking_at_screen": looking_at_screen,
                "head_pose": head_pose,
                "gaze_distance": gaze_distance,
                "eye_distance": eye_distance
            }
        except Exception as e:
            logging.error(f"Error in head pose analysis: {e}")
            return {"looking_at_screen": False, "head_pose": "unknown"}
    
    def detect_multiple_faces(self, frame):
        """Detect multiple faces and alert if more than one person"""
        # Use MediaPipe for better multiple face detection
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        face_count = 0
        if results.multi_face_landmarks:
            face_count = len(results.multi_face_landmarks)
        
        # Also check with OpenCV as backup
        opencv_faces = self.detect_faces_opencv(frame)
        opencv_face_count = len(opencv_faces)
        
        # Use the higher count
        final_face_count = max(face_count, opencv_face_count)
        
        return {
            "face_count": int(final_face_count),
            "multiple_faces_detected": bool(final_face_count > 1),
            "mediapipe_faces": int(face_count),
            "opencv_faces": int(opencv_face_count)
        }
    
    def analyze_eye_tracking(self, frame, face_landmarks):
        """Enhanced eye tracking analysis"""
        if not face_landmarks:
            return {"eye_state": "unknown", "eye_tracking": "unknown"}
        
        try:
            landmarks = face_landmarks.landmark
            h, w = frame.shape[:2]
            
            # Check if we have enough landmarks
            if len(landmarks) < 468:
                return {"eye_state": "unknown", "eye_tracking": "unknown"}
            
            # Get eye landmarks with bounds checking
            left_eye_points = [
                [float(landmarks[33].x * w), float(landmarks[33].y * h)] if len(landmarks) > 33 else [float(w/3), float(h/2)],  # Left eye left corner
                [float(landmarks[7].x * w), float(landmarks[7].y * h)] if len(landmarks) > 7 else [float(w/3), float(h/2-10)],    # Left eye top
                [float(landmarks[163].x * w), float(landmarks[163].y * h)] if len(landmarks) > 163 else [float(2*w/3), float(h/2)], # Left eye right corner
                [float(landmarks[145].x * w), float(landmarks[145].y * h)] if len(landmarks) > 145 else [float(w/3), float(h/2+10)]  # Left eye bottom
            ]
            
            right_eye_points = [
                [float(landmarks[263].x * w), float(landmarks[263].y * h)] if len(landmarks) > 263 else [float(2*w/3), float(h/2)], # Right eye left corner
                [float(landmarks[386].x * w), float(landmarks[386].y * h)] if len(landmarks) > 386 else [float(2*w/3), float(h/2-10)], # Right eye top
                [float(landmarks[362].x * w), float(landmarks[362].y * h)] if len(landmarks) > 362 else [float(w), float(h/2)], # Right eye right corner
                [float(landmarks[374].x * w), float(landmarks[374].y * h)] if len(landmarks) > 374 else [float(2*w/3), float(h/2+10)]  # Right eye bottom
            ]
            
            # Calculate eye aspect ratio (EAR) for both eyes
            def eye_aspect_ratio(eye_points):
                try:
                    # Vertical distances
                    A = dist.euclidean(eye_points[1], eye_points[3])
                    B = dist.euclidean(eye_points[0], eye_points[2])
                    # Horizontal distance
                    C = dist.euclidean(eye_points[0], eye_points[2])
                    # EAR
                    ear = (A + B) / (2.0 * C) if C > 0 else 0.3
                    return ear
                except Exception:
                    return 0.3  # Default value
            
            left_ear = eye_aspect_ratio(left_eye_points)
            right_ear = eye_aspect_ratio(right_eye_points)
            avg_ear = (left_ear + right_ear) / 2.0
            
            # Determine eye state
            if avg_ear < 0.2:
                eye_state = "closed"
            elif avg_ear < 0.25:
                eye_state = "blinking"
            else:
                eye_state = "open"
            
            # Eye tracking analysis
            left_eye_center = np.mean(left_eye_points, axis=0)
            right_eye_center = np.mean(right_eye_points, axis=0)
            eye_center = (left_eye_center + right_eye_center) / 2
            
            screen_center = np.array([w / 2, h / 2])
            eye_to_screen_distance = float(np.linalg.norm(eye_center - screen_center))
            
            # Determine if looking at screen
            screen_threshold = w * 0.3
            looking_at_screen = bool(eye_to_screen_distance < screen_threshold)
            
            return {
                "eye_state": eye_state,
                "eye_tracking": "looking_at_screen" if looking_at_screen else "looking_away",
                "eye_aspect_ratio": float(avg_ear),
                "eye_center": [float(x) for x in eye_center.tolist()],
                "screen_distance": eye_to_screen_distance
            }
        except Exception as e:
            logging.error(f"Error in eye tracking analysis: {e}")
            return {"eye_state": "unknown", "eye_tracking": "unknown"}
    
    def detect_screen_sharing(self, frame, analysis_data):
        """Detect if user is switching tabs/apps (simplified detection)"""
        # This is a simplified detection - in a real implementation,
        # you'd need to monitor system events or use browser APIs
        
        current_time = time.time()
        time_since_last_activity = current_time - self.last_activity_time
        
        # Detect potential screen switching based on sudden changes in face detection
        if analysis_data.get("face_detected"):
            self.last_activity_time = current_time
        
        # If no face detected for a while, might indicate switching
        if time_since_last_activity > 5.0 and not analysis_data.get("face_detected"):
            self.screen_sharing_detected = True
        else:
            self.screen_sharing_detected = False
        
        return {
            "screen_sharing_detected": bool(self.screen_sharing_detected),
            "time_since_last_activity": float(time_since_last_activity)
        }
    
    def analyze_voice_patterns(self, audio_data=None):
        """Analyze voice patterns for nervousness and confidence"""
        # Get voice analysis from the voice analysis service
        voice_state = voice_analysis_service.get_analysis_state()
        
        return {
            "speaking": bool(voice_state["speaking"]),
            "confidence": float(voice_state["confidence"]),
            "nervousness": float(voice_state["nervousness"]),
            "speech_patterns": list(voice_state["speech_patterns"])
        }
    
    def update_voice_analysis(self, voice_data):
        """Update voice analysis state from external source"""
        self.voice_analysis_state.update(voice_data)
    
    def process_frame(self, frame):
        """Process a frame and return comprehensive analysis data"""
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Initialize analysis data
        analysis_data = {
            "face_detected": False,
            "face_count": 0,
            "confidence": 0.0,
            "attention_score": 0.0,
            "engagement_level": "low",
            "eye_tracking": {},
            "head_pose": {},
            "multiple_faces": {},
            "screen_sharing": {},
            "voice_analysis": {},
            "suspicious_behavior": [],
            "recommendations": []
        }
        
        # Detect faces using MediaPipe
        face_detections = self.detect_faces_mediapipe(frame)
        
        # Fallback to OpenCV if MediaPipe fails
        if not face_detections:
            opencv_faces = self.detect_faces_opencv(frame)
            if opencv_faces:
                # Use OpenCV face detection as fallback
                largest_face = max(opencv_faces, key=lambda x: x[2] * x[3])
                x, y, w, h = largest_face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                confidence = 0.7  # Default confidence for OpenCV
                face_landmarks = None
            else:
                # No faces detected
                confidence = 0.0
                face_landmarks = None
        else:
            # Use MediaPipe detection
            detection = face_detections[0]
            bbox = detection.location_data.relative_bounding_box
            
            h, w = frame.shape[:2]
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            face_w = int(bbox.width * w)
            face_h = int(bbox.height * h)
            
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x + face_w, y + face_h), (255, 0, 0), 2)
            
            # Calculate confidence
            confidence = detection.score[0]
            
            # Get face landmarks for detailed analysis
            face_mesh_results = self.face_mesh.process(rgb_frame)
            face_landmarks = None
            if face_mesh_results.multi_face_landmarks:
                face_landmarks = face_mesh_results.multi_face_landmarks[0]
        
        # Perform analysis regardless of detection method
        if confidence > 0:
            # Analyze head pose
            head_pose_data = self.analyze_head_pose(frame, face_landmarks)
            
            # Analyze eye tracking
            eye_tracking_data = self.analyze_eye_tracking(frame, face_landmarks)
            
            # Detect multiple faces
            multiple_faces_data = self.detect_multiple_faces(frame)
            
            # Detect screen sharing
            screen_sharing_data = self.detect_screen_sharing(frame, analysis_data)
            
            # Analyze voice patterns
            voice_analysis_data = self.analyze_voice_patterns()
            
            # Calculate attention score
            attention_score = 0.0
            if head_pose_data["looking_at_screen"]:
                attention_score += 0.4
            if eye_tracking_data["eye_state"] == "open":
                attention_score += 0.3
            if eye_tracking_data["eye_tracking"] == "looking_at_screen":
                attention_score += 0.3
            
            # Determine engagement level
            if attention_score > 0.8 and confidence > 0.7:
                engagement_level = "high"
            elif attention_score > 0.5 and confidence > 0.5:
                engagement_level = "medium"
            else:
                engagement_level = "low"
            
            # Update analysis data
            analysis_data.update({
                "face_detected": True,
                "face_count": int(multiple_faces_data["face_count"]),
                "confidence": float(confidence),
                "attention_score": float(attention_score),
                "engagement_level": str(engagement_level),
                "eye_tracking": eye_tracking_data,
                "head_pose": head_pose_data,
                "multiple_faces": multiple_faces_data,
                "screen_sharing": screen_sharing_data,
                "voice_analysis": voice_analysis_data
            })
            
            # Generate recommendations and detect suspicious behavior
            recommendations = []
            suspicious_behavior = []
            
            # Head pose recommendations
            if not head_pose_data["looking_at_screen"]:
                recommendations.append("Please look directly at the camera")
                suspicious_behavior.append("User not looking at screen")
            
            if head_pose_data["head_pose"] in ["left", "right", "up", "down"]:
                recommendations.append(f"Please face the camera directly (currently looking {head_pose_data['head_pose']})")
                suspicious_behavior.append(f"Head turned {head_pose_data['head_pose']}")
            
            # Eye tracking recommendations
            if eye_tracking_data["eye_state"] == "closed":
                recommendations.append("Keep your eyes open and focused")
                suspicious_behavior.append("Eyes closed - may indicate inattention")
            
            if eye_tracking_data["eye_tracking"] == "looking_away":
                recommendations.append("Please look at the camera")
                suspicious_behavior.append("Eyes not focused on screen")
            
            # Multiple faces detection
            if multiple_faces_data["multiple_faces_detected"]:
                recommendations.append("Only one person should be visible in the camera")
                suspicious_behavior.append(f"Multiple faces detected ({multiple_faces_data['face_count']} people)")
            
            # Screen sharing detection
            if screen_sharing_data["screen_sharing_detected"]:
                recommendations.append("Please stay focused on the interview")
                suspicious_behavior.append("Potential screen switching detected")
            
            # Voice analysis recommendations
            if voice_analysis_data.get("nervousness", 0) > 0.7:
                recommendations.append("Try to speak more confidently and clearly")
                suspicious_behavior.append("High nervousness detected in voice")
            
            if voice_analysis_data.get("confidence", 0) < 0.3:
                recommendations.append("Speak with more confidence and clarity")
                suspicious_behavior.append("Low confidence detected in voice")
            
            # General engagement recommendations
            if engagement_level == "low":
                recommendations.append("Please maintain focus and engagement")
                suspicious_behavior.append("Low engagement detected")
            
            analysis_data["recommendations"] = recommendations
            analysis_data["suspicious_behavior"] = suspicious_behavior
            
            # No additional annotations - keep frame clean
            pass
        
        return frame, analysis_data

# Global enhanced face detection manager
enhanced_face_detector = EnhancedFaceDetector()

router = APIRouter(prefix="/face-detection", tags=["face-detection"])

class FaceDetectionManager:
    def __init__(self):
        self.camera = None
        self.is_streaming = False
        self.connections = {}
        self.camera_started = False
        
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
            annotated_frame, analysis_data = enhanced_face_detector.process_frame(frame)
            return annotated_frame, analysis_data
        except Exception as e:
            logging.error(f"Error processing frame: {e}")
            # Return a basic analysis with error state
            return frame, {
                "face_detected": False,
                "face_count": 0,
                "confidence": 0.0,
                "attention_score": 0.0,
                "engagement_level": "low",
                "eye_tracking": {"eye_state": "unknown", "eye_tracking": "unknown"},
                "head_pose": {"looking_at_screen": False, "head_pose": "unknown"},
                "multiple_faces": {"face_count": 0, "multiple_faces_detected": False},
                "screen_sharing": {"screen_sharing_detected": False, "time_since_last_activity": 0},
                "voice_analysis": {"speaking": False, "confidence": 0.0, "nervousness": 0.0, "speech_patterns": []},
                "suspicious_behavior": ["Face detection error"],
                "recommendations": ["Please check camera connection"],
                "error": str(e)
            }
    
    async def stream_video(self, websocket: WebSocket, client_id: str):
        """Stream video frames to the client"""
        try:
            print(f"🎥 Starting enhanced video stream for client {client_id}")
            
            self.is_streaming = True
            self.connections[client_id] = websocket
            print(f"✅ WebSocket connection established for client {client_id}")
            
            # Send initial connection success message
            await websocket.send_json({
                "type": "connected",
                "data": {
                    "message": "Enhanced face detection service connected successfully",
                    "camera_started": self.camera_started,
                    "features": [
                        "Eye tracking",
                        "Head pose detection", 
                        "Multiple face detection",
                        "Screen sharing detection",
                        "Voice analysis integration"
                    ]
                }
            })
            
            while self.is_streaming and client_id in self.connections:
                if self.camera and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret:
                        # Process the frame with enhanced analysis
                        annotated_frame, analysis_data = await self.process_frame(frame)
                        
                        # Encode frame to base64
                        _, buffer = cv2.imencode('.jpg', annotated_frame)
                        frame_bytes = base64.b64encode(buffer).decode('utf-8')
                        
                        # Send frame and comprehensive analysis data
                        try:
                            await websocket.send_json({
                                "type": "video_frame",
                                "data": {
                                    "image": frame_bytes,
                                    "analysis": analysis_data
                                }
                            })
                        except Exception as e:
                            import traceback
                            tb = traceback.format_exc()
                            print(f"❌ Error sending frame to client {client_id}: {e}\n{tb}")
                            import logging
                            logging.error(f"Error sending frame to client {client_id}: {e}\n{tb}")
                            # Attempt to notify client of error
                            try:
                                await websocket.send_json({
                                    "type": "error",
                                    "data": {"message": f"Error sending frame: {str(e)}"}
                                })
                            except Exception:
                                pass
                            try:
                                await websocket.close()
                            except Exception:
                                pass
                            break
                        
                        # Small delay to control frame rate
                        await asyncio.sleep(0.033)  # ~30 FPS
                    else:
                        print(f"⚠️ Failed to read frame from camera for client {client_id}")
                        await self.stop_camera()
                        await asyncio.sleep(1)
                        await self.start_camera()
                else:
                    if self.camera_started:
                        print(f"⚠️ Camera not available for client {client_id}")
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
    """WebSocket endpoint for enhanced face detection streaming"""
    try:
        print(f"🔌 WebSocket connection attempt from client {client_id}")
        await websocket.accept()
        print(f"✅ Client {client_id} connected to enhanced face detection")
        logging.info(f"Client {client_id} connected to enhanced face detection")
        
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

@router.post("/update-voice-analysis")
async def update_voice_analysis(voice_data: Dict[str, Any]):
    """Update voice analysis data from external source"""
    try:
        # Update voice analysis service with new data
        if "text_data" in voice_data:
            voice_analysis_service.update_voice_analysis(text_data=voice_data["text_data"])
        elif "audio_data" in voice_data:
            voice_analysis_service.update_voice_analysis(audio_data=voice_data["audio_data"])
        
        return {"status": "success", "message": "Voice analysis updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/start")
async def start_face_detection():
    """Start enhanced face detection service"""
    try:
        await face_manager.start_camera()
        return {"status": "success", "message": "Enhanced face detection started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/stop")
async def stop_face_detection():
    """Stop enhanced face detection service"""
    try:
        await face_manager.stop_camera()
        return {"status": "success", "message": "Enhanced face detection stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/status")
async def get_face_detection_status():
    """Get current enhanced face detection status"""
    return {
        "is_streaming": face_manager.is_streaming,
        "camera_available": face_manager.camera is not None and face_manager.camera.isOpened(),
        "camera_started": face_manager.camera_started,
        "active_connections": len(face_manager.connections),
        "features": [
            "Eye tracking",
            "Head pose detection",
            "Multiple face detection", 
            "Screen sharing detection",
            "Voice analysis integration"
        ]
    } 