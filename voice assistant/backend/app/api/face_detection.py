from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from typing import Any, Dict

import cv2
import mediapipe as mp
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from scipy.spatial import distance as dist

from app.services.voice_analysis import voice_analysis_service

logger = logging.getLogger("face-detection")
router = APIRouter(prefix="/face-detection", tags=["face-detection"])


# -----------------------------
# Enhanced Face Detector
# -----------------------------
class EnhancedFaceDetector:
    def __init__(self) -> None:
        # MediaPipe modules
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh

        # Instantiated processors
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=10,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # OpenCV cascades as fallback
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

        # Activity tracking (for simple “screen switching” heuristic)
        self.screen_sharing_detected = False
        self.last_activity_time = time.time()

    # ---- Face detection (MP + fallback) ----
    def detect_faces_mediapipe(self, frame: np.ndarray):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)
        return results.detections if results and results.detections else []

    def detect_faces_opencv(self, frame: np.ndarray):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return faces

    # ---- Head pose (simple heuristic using eye positions) ----
    def analyze_head_pose(self, frame: np.ndarray, face_landmarks) -> Dict[str, Any]:
        if not face_landmarks:
            return {"looking_at_screen": False, "head_pose": "unknown", "gaze_distance": 0.0}

        try:
            h, w = frame.shape[:2]
            landmarks = face_landmarks.landmark
            if len(landmarks) < 468:
                return {"looking_at_screen": False, "head_pose": "unknown", "gaze_distance": 0.0}

            # indices: 33 (left eye outer), 263 (right eye outer), 1 (nose)
            left_eye = np.array([landmarks[33].x * w, landmarks[33].y * h], dtype=float)
            right_eye = np.array([landmarks[263].x * w, landmarks[263].y * h], dtype=float)
            eye_center = (left_eye + right_eye) / 2.0

            screen_center = np.array([w / 2.0, h / 2.0], dtype=float)
            gaze_vector = eye_center - screen_center
            gaze_distance = float(np.linalg.norm(gaze_vector))
            looking_at_screen = gaze_distance < (w * 0.3)

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
                "looking_at_screen": bool(looking_at_screen),
                "head_pose": str(head_pose),
                "gaze_distance": float(gaze_distance),
            }
        except Exception as e:
            logger.exception("Error in head pose analysis: %s", e)
            return {"looking_at_screen": False, "head_pose": "unknown", "gaze_distance": 0.0}

    # ---- Multiple faces check ----
    def detect_multiple_faces(self, frame: np.ndarray) -> Dict[str, Any]:
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)

            mp_count = 0
            if results and getattr(results, "multi_face_landmarks", None):
                mp_count = len(results.multi_face_landmarks)

            ocv_faces = self.detect_faces_opencv(frame)
            ocv_count = len(ocv_faces) if ocv_faces is not None else 0

            final_count = max(int(mp_count), int(ocv_count))
            return {
                "face_count": final_count,
                "multiple_faces_detected": final_count > 1,
                "mediapipe_faces": int(mp_count),
                "opencv_faces": int(ocv_count),
            }
        except Exception as e:
            logger.exception("Error in detect_multiple_faces: %s", e)
            return {
                "face_count": 0,
                "multiple_faces_detected": False,
                "mediapipe_faces": 0,
                "opencv_faces": 0,
            }

    # ---- Eyes / gaze ----
    def analyze_eye_tracking(self, frame: np.ndarray, face_landmarks) -> Dict[str, Any]:
        if not face_landmarks:
            return {"eye_state": "unknown", "eye_tracking": "unknown", "eye_aspect_ratio": 0.0, "screen_distance": 0.0}

        try:
            h, w = frame.shape[:2]
            landmarks = face_landmarks.landmark
            if len(landmarks) < 468:
                return {"eye_state": "unknown", "eye_tracking": "unknown", "eye_aspect_ratio": 0.0, "screen_distance": 0.0}

            # landmark sets for rough EAR
            left_points = np.array(
                [
                    [landmarks[33].x * w, landmarks[33].y * h],   # left corner
                    [landmarks[7].x * w, landmarks[7].y * h],     # top
                    [landmarks[163].x * w, landmarks[163].y * h], # right corner
                    [landmarks[145].x * w, landmarks[145].y * h], # bottom
                ],
                dtype=float,
            )

            right_points = np.array(
                [
                    [landmarks[263].x * w, landmarks[263].y * h],
                    [landmarks[386].x * w, landmarks[386].y * h],
                    [landmarks[362].x * w, landmarks[362].y * h],
                    [landmarks[374].x * w, landmarks[374].y * h],
                ],
                dtype=float,
            )

            def ear(pts: np.ndarray) -> float:
                try:
                    A = dist.euclidean(pts[1], pts[3])  # vertical
                    B = dist.euclidean(pts[0], pts[2])  # diagonal (approx, for stability)
                    C = dist.euclidean(pts[0], pts[2])  # horizontal
                    return float((A + B) / (2.0 * C)) if C > 0 else 0.3
                except Exception:
                    return 0.3

            left_ear = ear(left_points)
            right_ear = ear(right_points)
            avg_ear = (left_ear + right_ear) / 2.0

            if avg_ear < 0.2:
                eye_state = "closed"
            elif avg_ear < 0.25:
                eye_state = "blinking"
            else:
                eye_state = "open"

            left_center = np.mean(left_points, axis=0)
            right_center = np.mean(right_points, axis=0)
            eye_center = (left_center + right_center) / 2.0

            screen_center = np.array([w / 2.0, h / 2.0], dtype=float)
            dist_to_center = float(np.linalg.norm(eye_center - screen_center))
            looking_at_screen = dist_to_center < (w * 0.3)

            return {
                "eye_state": str(eye_state),
                "eye_tracking": "looking_at_screen" if looking_at_screen else "looking_away",
                "eye_aspect_ratio": float(avg_ear),
                "screen_distance": float(dist_to_center),
            }
        except Exception as e:
            logger.exception("Error in eye tracking analysis: %s", e)
            return {"eye_state": "unknown", "eye_tracking": "unknown", "eye_aspect_ratio": 0.0, "screen_distance": 0.0}

    # ---- Simple tab/app switching heuristic ----
    def detect_screen_sharing(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        current_time = time.time()
        time_since_last = current_time - self.last_activity_time

        if analysis.get("face_detected"):
            self.last_activity_time = current_time

        self.screen_sharing_detected = bool(time_since_last > 5.0 and not analysis.get("face_detected"))

        return {
            "screen_sharing_detected": bool(self.screen_sharing_detected),
            "time_since_last_activity": float(time_since_last),
        }

    # ---- Voice analysis integration ----
    def analyze_voice_patterns(self) -> Dict[str, Any]:
        state = voice_analysis_service.get_analysis_state()
        return {
            "speaking": bool(state.get("speaking", False)),
            "confidence": float(state.get("confidence", 0.0)),
            "nervousness": float(state.get("nervousness", 0.0)),
            "speech_patterns": list(state.get("speech_patterns", [])),
        }

    # ---- Main per-frame processor ----
    def process_frame(self, frame: np.ndarray):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        analysis: Dict[str, Any] = {
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
            "recommendations": [],
        }

        face_dets = self.detect_faces_mediapipe(frame)
        face_landmarks = None
        confidence = 0.0

        if face_dets:
            det = face_dets[0]
            confidence = float(det.score[0] if det.score else 0.0)

            # get mesh landmarks for head/eye analysis
            face_mesh_results = self.face_mesh.process(rgb_frame)
            if face_mesh_results and face_mesh_results.multi_face_landmarks:
                face_landmarks = face_mesh_results.multi_face_landmarks[0]
        else:
            # fallback to OpenCV
            ocv_faces = self.detect_faces_opencv(frame)
            if ocv_faces is not None and len(ocv_faces) > 0:
                confidence = 0.7  # arbitrary default when using OpenCV fallback

        if confidence > 0.0:
            head_pose = self.analyze_head_pose(frame, face_landmarks)
            eye_track = self.analyze_eye_tracking(frame, face_landmarks)
            multi = self.detect_multiple_faces(frame)

            # temporarily mark face present to evaluate screen sharing heuristic
            analysis["face_detected"] = True
            analysis["face_count"] = int(multi["face_count"])
            analysis["confidence"] = float(confidence)

            # attention score
            attention_score = 0.0
            if head_pose.get("looking_at_screen"):
                attention_score += 0.4
            if eye_track.get("eye_state") == "open":
                attention_score += 0.3
            if eye_track.get("eye_tracking") == "looking_at_screen":
                attention_score += 0.3

            if attention_score > 0.8 and confidence > 0.7:
                engagement_level = "high"
            elif attention_score > 0.5 and confidence > 0.5:
                engagement_level = "medium"
            else:
                engagement_level = "low"

            analysis.update(
                {
                    "attention_score": float(attention_score),
                    "engagement_level": str(engagement_level),
                    "eye_tracking": eye_track,
                    "head_pose": head_pose,
                    "multiple_faces": multi,
                }
            )

            # screen sharing heuristic now that analysis is partly filled
            analysis["screen_sharing"] = self.detect_screen_sharing(analysis)

            # voice analysis
            voice_state = self.analyze_voice_patterns()
            analysis["voice_analysis"] = voice_state

            # recommendations + suspicious
            recs = []
            sus = []

            if not head_pose.get("looking_at_screen"):
                recs.append("Please look directly at the camera")
                sus.append("User not looking at screen")

            hp = head_pose.get("head_pose", "center")
            if hp in {"left", "right", "up", "down"}:
                recs.append(f"Please face the camera directly (currently looking {hp})")
                sus.append(f"Head turned {hp}")

            es = eye_track.get("eye_state")
            if es == "closed":
                recs.append("Keep your eyes open and focused")
                sus.append("Eyes closed - may indicate inattention")

            if eye_track.get("eye_tracking") == "looking_away":
                recs.append("Please look at the camera")
                sus.append("Eyes not focused on screen")

            if multi.get("multiple_faces_detected"):
                recs.append("Only one person should be visible in the camera")
                sus.append(f"Multiple faces detected ({multi.get('face_count', 0)} people)")

            if analysis["screen_sharing"].get("screen_sharing_detected"):
                recs.append("Please stay focused on the interview")
                sus.append("Potential screen switching detected")

            if voice_state.get("nervousness", 0.0) > 0.7:
                recs.append("Try to speak more confidently and clearly")
                sus.append("High nervousness detected in voice")

            if voice_state.get("confidence", 0.0) < 0.3:
                recs.append("Speak with more confidence and clarity")
                sus.append("Low confidence detected in voice")

            if engagement_level == "low":
                recs.append("Please maintain focus and engagement")
                sus.append("Low engagement detected")

            analysis["recommendations"] = recs
            analysis["suspicious_behavior"] = sus
        else:
            # when we couldn't detect a face
            analysis["screen_sharing"] = self.detect_screen_sharing(analysis)

        # Return the original frame (unannotated) and analysis
        return frame, analysis


enhanced_face_detector = EnhancedFaceDetector()


# -----------------------------
# Connections / Manager
# -----------------------------
class FaceDetectionManager:
    """Tracks connected clients. No physical camera is used (client sends frames)."""

    def __init__(self) -> None:
        self.is_streaming: bool = False
        self.connections: Dict[str, Dict[str, Any]] = {}

    async def start_camera(self) -> None:
        # Semantic: mark the service as "ready/streaming". We don't use a local camera.
        if not self.is_streaming:
            logger.info("Starting face detection streaming (client-provided frames).")
            self.is_streaming = True

    async def stop_camera(self) -> None:
        if self.is_streaming:
            logger.info("Stopping face detection streaming.")
            self.is_streaming = False


face_manager = FaceDetectionManager()


# -----------------------------
# WebSocket endpoint
# -----------------------------
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Accepts base64-encoded image frames from the client and returns analysis."""
    await websocket.accept()
    logger.info("Client %s connected to enhanced face detection", client_id)

    face_manager.connections[client_id] = {"websocket": websocket, "last_active": time.time()}
    try:
        while True:
            msg = await websocket.receive_json()
            msg_type = msg.get("type")

            if msg_type == "video_frame":
                frame_data = msg.get("data", {})
                image_b64 = frame_data.get("image")
                if not image_b64:
                    # ignore empty payloads
                    continue

                try:
                    # decode base64 image
                    header, encoded = image_b64.split(",", 1) if "," in image_b64 else ("", image_b64)
                    binary = base64.b64decode(encoded)
                    nparr = np.frombuffer(binary, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is None:
                        continue

                    _, analysis = enhanced_face_detector.process_frame(frame)

                    await websocket.send_json(
                        {
                            "type": "analysis_result",
                            "data": {"analysis": analysis, "timestamp": time.time()},
                        }
                    )
                except Exception as e:
                    logger.exception("Error processing incoming frame: %s", e)
                    await websocket.send_json(
                        {
                            "type": "analysis_result",
                            "data": {
                                "analysis": {
                                    "face_detected": False,
                                    "face_count": 0,
                                    "confidence": 0.0,
                                    "attention_score": 0.0,
                                    "engagement_level": "low",
                                    "eye_tracking": {"eye_state": "unknown", "eye_tracking": "unknown"},
                                    "head_pose": {"looking_at_screen": False, "head_pose": "unknown"},
                                    "multiple_faces": {"face_count": 0, "multiple_faces_detected": False},
                                    "screen_sharing": {"screen_sharing_detected": False, "time_since_last_activity": 0.0},
                                    "voice_analysis": {"speaking": False, "confidence": 0.0, "nervousness": 0.0, "speech_patterns": []},
                                    "suspicious_behavior": ["Frame processing error"],
                                    "recommendations": ["Please check camera connection"],
                                    "error": str(e),
                                },
                                "timestamp": time.time(),
                            },
                        }
                    )

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            # throttle loop a bit to avoid pegging CPU if client spams
            await asyncio.sleep(0)

    except WebSocketDisconnect:
        logger.info("Client %s disconnected", client_id)
    except Exception as e:
        logger.exception("WebSocket error for client %s: %s", client_id, e)
    finally:
        face_manager.connections.pop(client_id, None)
        logger.info("Removed client %s from connections", client_id)


# -----------------------------
# REST endpoints
# -----------------------------
@router.post("/start")
async def start_face_detection():
    try:
        await face_manager.start_camera()
        return {"status": "success", "message": "Enhanced face detection started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/stop")
async def stop_face_detection():
    try:
        await face_manager.stop_camera()
        return {"status": "success", "message": "Enhanced face detection stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/start-camera/{client_id}")
async def start_camera_for_client(client_id: str):
    try:
        if client_id in face_manager.connections:
            await face_manager.start_camera()
            return {"status": "success", "message": "Camera started successfully"}
        return {"status": "error", "message": "Client not connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/stop-camera/{client_id}")
async def stop_camera_for_client(client_id: str):
    try:
        if client_id in face_manager.connections:
            await face_manager.stop_camera()
            return {"status": "success", "message": "Camera stopped successfully"}
        return {"status": "error", "message": "Client not connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/update-voice-analysis")
async def update_voice_analysis(voice_data: Dict[str, Any]):
    """Pass text or audio-derived info to the voice analysis service."""
    try:
        if "text_data" in voice_data:
            voice_analysis_service.update_voice_analysis(text_data=voice_data["text_data"])
        elif "audio_data" in voice_data:
            voice_analysis_service.update_voice_analysis(audio_data=voice_data["audio_data"])
        return {"status": "success", "message": "Voice analysis updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/status")
async def get_face_detection_status():
    """Return the service status (no local camera used; client supplies frames)."""
    return {
        "is_streaming": face_manager.is_streaming,
        "camera_available": False,  # no local camera used
        "camera_started": face_manager.is_streaming,
        "active_connections": len(face_manager.connections),
        "features": [
            "Eye tracking",
            "Head pose detection",
            "Multiple face detection",
            "Screen sharing detection",
            "Voice analysis integration",
        ],
    }
