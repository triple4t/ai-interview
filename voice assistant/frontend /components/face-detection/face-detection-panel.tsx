"use client";

import React, {
  useEffect,
  useRef,
  useState,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Camera, Eye, Smiley, Warning, X } from "@phosphor-icons/react";

interface AnalysisData {
  emotion?: string;
  eye_state?: string;
  face_detected?: boolean;
  confidence?: number;
  attention_score?: number;
  engagement_level?: string;
  recommendations?: string[];
  suspicious_behavior?: string[];
  eye_tracking?: {
    eye_state?: string;
    eye_tracking?: string;
    eye_aspect_ratio?: number;
    screen_distance?: number;
  };
  head_pose?: {
    looking_at_screen?: boolean;
    head_pose?: string;
    gaze_distance?: number;
  };
  multiple_faces?: {
    face_count?: number;
    multiple_faces_detected?: boolean;
  };
  screen_sharing?: {
    screen_sharing_detected?: boolean;
    time_since_last_activity?: number;
  };
  voice_analysis?: {
    speaking?: boolean;
    confidence?: number;
    nervousness?: number;
    speech_patterns?: string[];
  };
}

interface FaceDetectionPanelProps {
  isActive: boolean;
  onToggle: () => void;
  className?: string;
  shouldStartCamera?: boolean;
  onAnalysisDataChange?: (data: AnalysisData) => void;
}

export const FaceDetectionPanel = forwardRef<
  { forceDisconnect: () => void },
  FaceDetectionPanelProps
>(function FaceDetectionPanel(
  {
    isActive,
    onToggle,
    className = "",
    shouldStartCamera = false,
    onAnalysisDataChange,
  },
  ref
) {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cameraStarted, setCameraStarted] = useState(false);
  const [analysisData, setAnalysisData] = useState<AnalysisData>({});

  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null); // visible preview
  const canvasRef = useRef<HTMLCanvasElement | null>(null); // offscreen for encoding
  const rafIdRef = useRef<number | null>(null);
  const pingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastSentRef = useRef<number>(0);
  const clientId = useRef(
    `client_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`
  );
  const retryCountRef = useRef(0);
  const MAX_RETRIES = 3;
  const TARGET_FPS = 10; // ~10fps upstream

  // Expose a hard disconnect to parent
  const forceDisconnect = useCallback(() => {
    setError(null);
    stopCamera();
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {}
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
    setIsLoading(false);
    retryCountRef.current = 0;
    setAnalysisData({});
  }, []);

  useImperativeHandle(ref, () => ({ forceDisconnect }), [forceDisconnect]);

  const clearPing = () => {
    if (pingTimerRef.current) {
      clearInterval(pingTimerRef.current);
      pingTimerRef.current = null;
    }
  };
  const startPing = () => {
    clearPing();
    pingTimerRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 15000);
  };

  const stopCamera = useCallback(() => {
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    if (videoRef.current) {
      try {
        videoRef.current.pause();
        videoRef.current.srcObject = null;
      } catch {}
    }
    if (streamRef.current) {
      try {
        streamRef.current.getTracks().forEach((t) => t.stop());
      } catch {}
    }
    streamRef.current = null;
    setCameraStarted(false);
  }, []);

  const frameLoop = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      rafIdRef.current = null;
      return;
    }

    const now = performance.now();
    const minInterval = 1000 / TARGET_FPS;
    if (now - lastSentRef.current < minInterval) {
      rafIdRef.current = requestAnimationFrame(frameLoop);
      return;
    }

    const video = videoRef.current;
    let canvas = canvasRef.current;
    if (!video || video.readyState < 2) {
      rafIdRef.current = requestAnimationFrame(frameLoop);
      return;
    }
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvasRef.current = canvas;
    }
    const w = video.videoWidth || 640;
    const h = video.videoHeight || 480;
    if (canvas.width !== w) canvas.width = w;
    if (canvas.height !== h) canvas.height = h;

    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (ctx) {
      ctx.drawImage(video, 0, 0, w, h);
      try {
        const frameData = canvas.toDataURL("image/jpeg", 0.7);
        wsRef.current.send(
          JSON.stringify({
            type: "video_frame",
            data: {
              image: frameData,
              timestamp: Date.now(),
              client_id: clientId.current,
            },
          })
        );
        lastSentRef.current = now;
      } catch {}
    }
    rafIdRef.current = requestAnimationFrame(frameLoop);
  }, []);

  const startCamera = useCallback(async () => {
    if (cameraStarted) return;
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user",
        },
        audio: false,
      });

      if (!videoRef.current) {
        setError("Video element not ready.");
        return;
      }
      videoRef.current.autoplay = true;
      videoRef.current.muted = true;
      videoRef.current.playsInline = true;
      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      streamRef.current = stream;
      setCameraStarted(true);
      rafIdRef.current = requestAnimationFrame(frameLoop);
    } catch (err) {
      console.error("Camera error:", err);
      setError(
        "Failed to access camera. Please allow permissions and try again."
      );
      stopCamera();
    }
  }, [cameraStarted, frameLoop, stopCamera]);

  const connectWebSocket = useCallback(() => {
    if (isConnecting || isConnected || wsRef.current) return;

    setIsConnecting(true);
    setIsLoading(true);
    setError(null);

    const wsUrl = `ws://localhost:8000/api/v1/face-detection/ws/${clientId.current}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      wsRef.current = ws;
      setIsConnecting(false);
      setIsLoading(false);
      setIsConnected(true);
      retryCountRef.current = 0;
      startPing();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "analysis_result") {
          const newAnalysis: AnalysisData = data.data?.analysis ?? {};
          setAnalysisData(newAnalysis);
          onAnalysisDataChange?.(newAnalysis);
        } else if (data.type === "error") {
          setError(data.message || "Face detection error");
        }
      } catch (e) {
        console.error("WS parse error:", e);
      }
    };

    ws.onerror = () => {
      setError("Failed to connect to face detection service.");
    };

    ws.onclose = () => {
      clearPing();
      setIsConnected(false);
      setIsConnecting(false);
      setIsLoading(false);
      wsRef.current = null;
      stopCamera();
      setCameraStarted(false);

      if (isActive && retryCountRef.current < MAX_RETRIES) {
        retryCountRef.current += 1;
        setTimeout(() => {
          connectWebSocket();
        }, 1500);
      } else if (isActive && retryCountRef.current >= MAX_RETRIES) {
        setError("Unable to connect after multiple attempts.");
      }
    };
  }, [isActive, isConnecting, isConnected, onAnalysisDataChange, stopCamera]);

  // Lifecycle: connect/disconnect WS
  useEffect(() => {
    if (isActive) {
      connectWebSocket();
    } else {
      forceDisconnect();
    }
    return () => {
      forceDisconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive]);

  // Start/stop camera based on prop + connection
  useEffect(() => {
    if (shouldStartCamera && isConnected && !cameraStarted) {
      startCamera();
    } else if ((!shouldStartCamera || !isConnected) && cameraStarted) {
      stopCamera();
    }
  }, [shouldStartCamera, isConnected, cameraStarted, startCamera, stopCamera]);

  // UI helpers
  const getEmotionColor = (emotion?: string) => {
    switch ((emotion || "").toLowerCase()) {
      case "happy":
        return "bg-green-100 text-green-800";
      case "sad":
        return "bg-blue-100 text-blue-800";
      case "angry":
        return "bg-red-100 text-red-800";
      case "neutral":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };
  const getEyeStateColor = (eyeState?: string) => {
    switch ((eyeState || "").toLowerCase()) {
      case "open":
        return "bg-green-100 text-green-800";
      case "closed":
        return "bg-red-100 text-red-800";
      case "blinking":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };
  const getEngagementColor = (level?: string) => {
    switch ((level || "").toLowerCase()) {
      case "high":
        return "bg-green-100 text-green-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "low":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <AnimatePresence>
      {isActive && (
        <motion.div
          initial={{ opacity: 0, x: 300 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 300 }}
          transition={{ duration: 0.25 }}
          className={`fixed right-4 top-4 w-80 z-50 ${className}`}
        >
          <Card className="shadow-lg border-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Camera size={20} />
                  Face Analysis
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onToggle}
                  className="h-8 w-8 p-0"
                >
                  <X size={16} />
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Connection Status */}
              <div className="flex items-center gap-2">
                <div
                  className={`w-3 h-3 rounded-full ${
                    isConnected ? "bg-green-500" : "bg-red-500"
                  }`}
                />
                <span className="text-sm font-medium">
                  {isConnected ? "Connected" : "Disconnected"}
                </span>
                {isLoading && (
                  <span className="text-sm text-muted-foreground">
                    Connecting...
                  </span>
                )}
              </div>

              {/* Error */}
              {error && (
                <Alert variant="destructive">
                  <Warning size={16} />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Visible Camera Preview */}
              <div className="relative">
                <video
                  ref={videoRef}
                  className="w-full h-48 object-cover rounded-lg border bg-black"
                  playsInline
                  muted
                  autoPlay
                />
                {cameraStarted && analysisData.face_detected === false && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40 rounded-lg">
                    <div className="text-white text-xs">No face detected</div>
                  </div>
                )}
                {!cameraStarted && !error && (
                  <div className="absolute inset-0 flex items-center justify-center text-white/80 text-sm">
                    {isConnected
                      ? "Camera not started yet…"
                      : "Waiting for connection…"}
                  </div>
                )}
              </div>

              {/* Analysis */}
              {Object.keys(analysisData).length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Face Detected:</span>
                    <Badge
                      variant={analysisData.face_detected ? "default" : "secondary"}
                    >
                      {analysisData.face_detected ? "Yes" : "No"}
                    </Badge>
                  </div>

                  {analysisData.emotion && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium flex items-center gap-1">
                        <Smiley size={16} />
                        Emotion:
                      </span>
                      <Badge className={getEmotionColor(analysisData.emotion)}>
                        {analysisData.emotion}
                      </Badge>
                    </div>
                  )}

                  {analysisData.eye_state && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium flex items-center gap-1">
                        <Eye size={16} />
                        Eye State:
                      </span>
                      <Badge className={getEyeStateColor(analysisData.eye_state)}>
                        {analysisData.eye_state}
                      </Badge>
                    </div>
                  )}

                  {analysisData.engagement_level && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Engagement:</span>
                      <Badge
                        className={getEngagementColor(
                          analysisData.engagement_level
                        )}
                      >
                        {analysisData.engagement_level}
                      </Badge>
                    </div>
                  )}

                  {typeof analysisData.confidence === "number" && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Confidence:</span>
                      <span className="text-sm text-muted-foreground">
                        {Math.round(analysisData.confidence * 100)}%
                      </span>
                    </div>
                  )}

                  {typeof analysisData.attention_score === "number" && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Attention:</span>
                      <span className="text-sm text-muted-foreground">
                        {Math.round(analysisData.attention_score * 100)}%
                      </span>
                    </div>
                  )}

                  {/* Enhanced */}
                  <div className="border-t pt-3 mt-3">
                    <h4 className="text-sm font-medium mb-2 text-blue-600">
                      Enhanced Analysis
                    </h4>

                    {analysisData.eye_tracking && (
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">
                            Eye Tracking:
                          </span>
                          <Badge
                            variant={
                              analysisData.eye_tracking.eye_tracking ===
                              "looking_at_screen"
                                ? "default"
                                : "secondary"
                            }
                          >
                            {analysisData.eye_tracking.eye_tracking || "unknown"}
                          </Badge>
                        </div>
                        {typeof analysisData.eye_tracking.eye_aspect_ratio ===
                          "number" && (
                          <div className="flex items-center justify-between">
                            <span className="text-xs">Eye Aspect Ratio:</span>
                            <span className="text-xs text-muted-foreground">
                              {analysisData.eye_tracking.eye_aspect_ratio.toFixed(
                                3
                              )}
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {analysisData.head_pose && (
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">Head Pose:</span>
                          <Badge
                            variant={
                              analysisData.head_pose.looking_at_screen
                                ? "default"
                                : "secondary"
                            }
                          >
                            {analysisData.head_pose.head_pose || "unknown"}
                          </Badge>
                        </div>
                        {typeof analysisData.head_pose.gaze_distance ===
                          "number" && (
                          <div className="flex items-center justify-between">
                            <span className="text-xs">Gaze Distance:</span>
                            <span className="text-xs text-muted-foreground">
                              {Math.round(analysisData.head_pose.gaze_distance)}px
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {analysisData.multiple_faces && (
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">Face Count:</span>
                          <Badge
                            variant={
                              analysisData.multiple_faces
                                .multiple_faces_detected
                                ? "destructive"
                                : "default"
                            }
                          >
                            {analysisData.multiple_faces.face_count || 0}
                          </Badge>
                        </div>
                        {analysisData.multiple_faces.multiple_faces_detected && (
                          <div className="text-xs text-red-600">
                            ⚠️ Multiple people detected
                          </div>
                        )}
                      </div>
                    )}

                    {analysisData.screen_sharing && (
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">
                            Screen Activity:
                          </span>
                          <Badge
                            variant={
                              analysisData.screen_sharing
                                .screen_sharing_detected
                                ? "destructive"
                                : "default"
                            }
                          >
                            {analysisData.screen_sharing
                              .screen_sharing_detected
                              ? "Switching"
                              : "Focused"}
                          </Badge>
                        </div>
                        {typeof analysisData.screen_sharing
                          .time_since_last_activity === "number" && (
                          <div className="flex items-center justify-between">
                            <span className="text-xs">Last Activity:</span>
                            <span className="text-xs text-muted-foreground">
                              {Math.round(
                                analysisData.screen_sharing
                                  .time_since_last_activity
                              )}
                              s ago
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {analysisData.voice_analysis && (
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">Voice:</span>
                          <Badge
                            variant={
                              analysisData.voice_analysis.speaking
                                ? "default"
                                : "secondary"
                            }
                          >
                            {analysisData.voice_analysis.speaking
                              ? "Speaking"
                              : "Silent"}
                          </Badge>
                        </div>
                        {typeof analysisData.voice_analysis.confidence ===
                          "number" && (
                          <div className="flex items-center justify-between">
                            <span className="text-xs">Confidence:</span>
                            <span className="text-xs text-muted-foreground">
                              {Math.round(
                                analysisData.voice_analysis.confidence * 100
                              )}
                              %
                            </span>
                          </div>
                        )}
                        {typeof analysisData.voice_analysis.nervousness ===
                          "number" && (
                          <div className="flex items-center justify-between">
                            <span className="text-xs">Nervousness:</span>
                            <span className="text-xs text-muted-foreground">
                              {Math.round(
                                analysisData.voice_analysis.nervousness * 100
                              )}
                              %
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Recommendations */}
                  {analysisData.recommendations &&
                    analysisData.recommendations.length > 0 && (
                      <div className="mt-3">
                        <h4 className="text-sm font-medium mb-2">
                          Recommendations:
                        </h4>
                        <ul className="text-xs text-muted-foreground space-y-1">
                          {analysisData.recommendations.map((rec, i) => (
                            <li key={i} className="flex items-start gap-1">
                              <span className="text-blue-500">•</span>
                              {rec}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                  {/* Suspicious Behavior */}
                  {analysisData.suspicious_behavior &&
                    analysisData.suspicious_behavior.length > 0 && (
                      <div className="mt-3">
                        <h4 className="text-sm font-medium mb-2 text-red-600">
                          ⚠️ Suspicious Behavior:
                        </h4>
                        <ul className="text-xs text-red-600 space-y-1">
                          {analysisData.suspicious_behavior.map((b, i) => (
                            <li key={i} className="flex items-start gap-1">
                              <span className="text-red-500">⚠</span>
                              {b}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
});
