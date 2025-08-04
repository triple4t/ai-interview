"use client";

import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Camera, Eye, Smiley, Warning, X } from '@phosphor-icons/react';

interface AnalysisData {
  emotion?: string;
  eye_state?: string;
  face_detected?: boolean;
  confidence?: number;
  attention_score?: number;
  engagement_level?: string;
  recommendations?: string[];
  suspicious_behavior?: string[];
  // Enhanced features
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
  shouldStartCamera?: boolean; // New prop to control when camera should start
  onAnalysisDataChange?: (data: AnalysisData) => void; // New prop to pass analysis data to parent
}

export const FaceDetectionPanel = React.forwardRef<{ forceDisconnect: () => void }, FaceDetectionPanelProps>(({
  isActive,
  onToggle,
  className = "",
  shouldStartCamera = false,
  onAnalysisDataChange
}, ref) => {
  const [isConnected, setIsConnected] = useState(false);
  const [analysisData, setAnalysisData] = useState<AnalysisData>({});
  const [videoFrame, setVideoFrame] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [cameraStarted, setCameraStarted] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [debouncedIsActive, setDebouncedIsActive] = useState(false);
  const [shouldDisconnect, setShouldDisconnect] = useState(false); // New state to control disconnection

  const wsRef = useRef<WebSocket | null>(null);
  const clientId = useRef(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const maxRetries = 3;

  // Debounce the isActive prop to prevent rapid state changes
  useEffect(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(() => {
      setDebouncedIsActive(isActive);
    }, 500); // 500ms debounce

    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, [isActive]);

  // Function to explicitly disconnect (called from parent)
  const forceDisconnect = () => {
    console.log('🛑 Force disconnecting face detection');
    setShouldDisconnect(true);
    disconnectWebSocket();
  };

  // Expose forceDisconnect to parent component
  React.useImperativeHandle(ref, () => ({
    forceDisconnect
  }));

  const connectWebSocket = () => {
    if (isConnecting || isConnected) {
      console.log('🔄 Already connecting or connected, skipping connection attempt');
      return;
    }

    try {
      setIsConnecting(true);
      setError(null);

      // Always use ws:// for localhost development
      const wsUrl = `ws://localhost:8000/api/v1/face-detection/ws/${clientId.current}`;
      console.log('🔌 Attempting to connect to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'video_frame') {
            setVideoFrame(data.data.image);
            const newAnalysisData = data.data.analysis || {};
            setAnalysisData(newAnalysisData);
            
            // Pass analysis data to parent component
            if (onAnalysisDataChange) {
              onAnalysisDataChange(newAnalysisData);
            }
          } else if (data.type === 'connected') {
            console.log('✅ Face detection service connected:', data.data.message);
            // Don't start camera immediately - wait for shouldStartCamera prop
          } else if (data.type === 'error') {
            console.error('❌ Face detection error:', data.data.message);
            setError(data.data.message);
            setIsConnected(false);
            setIsLoading(false);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current = ws;

      // Add connection timeout
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.error('WebSocket connection timeout');
          ws.close();
          setError('Connection timeout - please try again');
          setIsLoading(false);
          setIsConnecting(false);
        }
      }, 5000); // 5 second timeout

      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        console.log('✅ Face detection WebSocket connected successfully');
        setIsConnected(true);
        setError(null);
        setIsLoading(false);
        setIsConnecting(false);
        retryCountRef.current = 0; // Reset retry counter on successful connection
        
        // Don't start camera immediately - wait for shouldStartCamera prop
      };

      ws.onerror = (error) => {
        clearTimeout(connectionTimeout);
        console.error('❌ WebSocket error:', error);
        setError('Failed to connect to face detection service');
        setIsLoading(false);
        setIsConnecting(false);
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        clearTimeout(connectionTimeout);
        console.log('🔌 WebSocket connection closed', event.code, event.reason);
        setIsConnected(false);
        setVideoFrame(null);
        setAnalysisData({});
        setCameraStarted(false);
        setIsConnecting(false);

        // Clear any existing reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };
    } catch (error) {
      console.error('❌ Error creating WebSocket:', error);
      setError('Failed to initialize face detection');
      setIsLoading(false);
      setIsConnecting(false);
    }
  };

  const startCamera = async () => {
    if (!isConnected) {
      console.log('⚠️ Cannot start camera - not connected to WebSocket');
      return;
    }

    try {
      console.log('🎥 Starting camera for face detection...');
      const response = await fetch(`http://localhost:8000/api/v1/face-detection/start-camera/${clientId.current}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        console.log('✅ Camera started successfully');
        setCameraStarted(true);
      } else {
        console.error('❌ Failed to start camera');
        setError('Failed to start camera');
      }
    } catch (error) {
      console.error('❌ Error starting camera:', error);
      setError('Failed to start camera');
    }
  };

  const stopCamera = async () => {
    try {
      console.log('🛑 Stopping camera...');
      const response = await fetch(`http://localhost:8000/api/v1/face-detection/stop-camera/${clientId.current}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        console.log('✅ Camera stopped successfully');
        setCameraStarted(false);
      } else {
        console.error('❌ Failed to stop camera');
      }
    } catch (error) {
      console.error('❌ Error stopping camera:', error);
    }
  };

  const disconnectWebSocket = () => {
    // Clear any reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Clear debounce timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }

    // Stop camera first
    stopCamera();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setVideoFrame(null);
    setAnalysisData({});
    setCameraStarted(false);
    setIsConnecting(false);
    retryCountRef.current = 0; // Reset retry counter when disconnecting
  };

  // Effect to start camera when shouldStartCamera becomes true
  useEffect(() => {
    if (shouldStartCamera && isConnected && !cameraStarted) {
      console.log('🎯 Starting camera - interview has begun');
      startCamera();
    } else if (!shouldStartCamera && cameraStarted) {
      console.log('🛑 Stopping camera - interview ended');
      stopCamera();
    }
  }, [shouldStartCamera, isConnected, cameraStarted]);

  // Effect to handle WebSocket connection based on isActive
  // Only disconnect if explicitly told to do so (shouldDisconnect is true)
  useEffect(() => {
    if (debouncedIsActive && !isConnected && !isConnecting && !isLoading && !shouldDisconnect) {
      console.log('🔄 Activating face detection...');
      setIsLoading(true);

      // Add a small delay to ensure backend is ready
      setTimeout(() => {
        connectWebSocket();
      }, 100);
    } else if (shouldDisconnect && isConnected) {
      console.log('🛑 Force disconnecting face detection...');
      disconnectWebSocket();
      setShouldDisconnect(false); // Reset the flag
    }

    return () => {
      if (shouldDisconnect) {
        disconnectWebSocket();
      }
    };
  }, [debouncedIsActive, isConnected, isConnecting, isLoading, shouldDisconnect]);

  // Add a retry mechanism for failed connections
  useEffect(() => {
    if (debouncedIsActive && !isConnected && !isConnecting && error && retryCountRef.current < maxRetries && !shouldDisconnect) {
      console.log(`🔄 Retrying connection after error (attempt ${retryCountRef.current + 1}/${maxRetries})...`);
      
      // Clear error and retry after 2 seconds
      setTimeout(() => {
        retryCountRef.current += 1;
        setError(null);
        setIsLoading(true);
        connectWebSocket();
      }, 2000);
    } else if (retryCountRef.current >= maxRetries) {
      console.log('❌ Max retries reached, giving up on face detection connection');
      setError('Failed to connect after multiple attempts. Please refresh the page.');
    }
  }, [debouncedIsActive, isConnected, isConnecting, error, shouldDisconnect]);

  // Prevent rapid reconnection attempts - only if not explicitly disconnecting
  useEffect(() => {
    if (!debouncedIsActive && isConnected && !shouldDisconnect) {
      console.log('🛑 Face detection deactivated, disconnecting...');
      disconnectWebSocket();
    }
  }, [debouncedIsActive, isConnected, shouldDisconnect]);

  const getEmotionColor = (emotion?: string) => {
    switch (emotion?.toLowerCase()) {
      case 'happy':
        return 'bg-green-100 text-green-800';
      case 'sad':
        return 'bg-blue-100 text-blue-800';
      case 'angry':
        return 'bg-red-100 text-red-800';
      case 'neutral':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getEyeStateColor = (eyeState?: string) => {
    switch (eyeState?.toLowerCase()) {
      case 'open':
        return 'bg-green-100 text-green-800';
      case 'closed':
        return 'bg-red-100 text-red-800';
      case 'blinking':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getEngagementColor = (level?: string) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <AnimatePresence>
      {debouncedIsActive && (
        <motion.div
          initial={{ opacity: 0, x: 300 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 300 }}
          transition={{ duration: 0.3 }}
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
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm font-medium">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
                {isLoading && (
                  <span className="text-sm text-muted-foreground">Connecting...</span>
                )}
              </div>

              {/* Error Display */}
              {error && (
                <Alert variant="destructive">
                  <Warning size={16} />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Video Frame */}
              {videoFrame && (
                <div className="relative">
                  <img
                    src={`data:image/jpeg;base64,${videoFrame}`}
                    alt="Face detection"
                    className="w-full h-48 object-cover rounded-lg border"
                  />
                  {!analysisData.face_detected && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-lg">
                      <div className="text-white text-center">
                        <Warning size={32} className="mx-auto mb-2" />
                        <p className="text-sm">No face detected</p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Analysis Data */}
              {Object.keys(analysisData).length > 0 && (
                <div className="space-y-3">
                  {/* Face Detection Status */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Face Detected:</span>
                    <Badge variant={analysisData.face_detected ? "default" : "secondary"}>
                      {analysisData.face_detected ? 'Yes' : 'No'}
                    </Badge>
                  </div>

                  {/* Emotion */}
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

                  {/* Eye State */}
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

                  {/* Engagement Level */}
                  {analysisData.engagement_level && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Engagement:</span>
                      <Badge className={getEngagementColor(analysisData.engagement_level)}>
                        {analysisData.engagement_level}
                      </Badge>
                    </div>
                  )}

                  {/* Confidence Score */}
                  {analysisData.confidence && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Confidence:</span>
                      <span className="text-sm text-muted-foreground">
                        {Math.round(analysisData.confidence * 100)}%
                      </span>
                    </div>
                  )}

                  {/* Attention Score */}
                  {analysisData.attention_score && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Attention Score:</span>
                      <span className="text-sm text-muted-foreground">
                        {Math.round(analysisData.attention_score * 100)}%
                      </span>
                    </div>
                  )}

                  {/* Enhanced Features */}
                  <div className="border-t pt-3 mt-3">
                    <h4 className="text-sm font-medium mb-2 text-blue-600">Enhanced Analysis</h4>
                    
                    {/* Eye Tracking */}
                    {analysisData.eye_tracking && (
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">Eye Tracking:</span>
                          <Badge variant={analysisData.eye_tracking.eye_tracking === 'looking_at_screen' ? 'default' : 'secondary'}>
                            {analysisData.eye_tracking.eye_tracking || 'unknown'}
                          </Badge>
                        </div>
                        {analysisData.eye_tracking.eye_aspect_ratio && (
                          <div className="flex items-center justify-between">
                            <span className="text-xs">Eye Aspect Ratio:</span>
                            <span className="text-xs text-muted-foreground">
                              {analysisData.eye_tracking.eye_aspect_ratio.toFixed(3)}
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Head Pose */}
                    {analysisData.head_pose && (
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">Head Pose:</span>
                          <Badge variant={analysisData.head_pose.looking_at_screen ? 'default' : 'secondary'}>
                            {analysisData.head_pose.head_pose || 'unknown'}
                          </Badge>
                        </div>
                        {analysisData.head_pose.gaze_distance && (
                          <div className="flex items-center justify-between">
                            <span className="text-xs">Gaze Distance:</span>
                            <span className="text-xs text-muted-foreground">
                              {Math.round(analysisData.head_pose.gaze_distance)}px
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Multiple Faces */}
                    {analysisData.multiple_faces && (
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">Face Count:</span>
                          <Badge variant={analysisData.multiple_faces.multiple_faces_detected ? 'destructive' : 'default'}>
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

                    {/* Screen Sharing Detection */}
                    {analysisData.screen_sharing && (
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">Screen Activity:</span>
                          <Badge variant={analysisData.screen_sharing.screen_sharing_detected ? 'destructive' : 'default'}>
                            {analysisData.screen_sharing.screen_sharing_detected ? 'Switching' : 'Focused'}
                          </Badge>
                        </div>
                        {analysisData.screen_sharing.time_since_last_activity && (
                          <div className="flex items-center justify-between">
                            <span className="text-xs">Last Activity:</span>
                            <span className="text-xs text-muted-foreground">
                              {Math.round(analysisData.screen_sharing.time_since_last_activity)}s ago
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Voice Analysis */}
                    {analysisData.voice_analysis && (
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">Voice Status:</span>
                          <Badge variant={analysisData.voice_analysis.speaking ? 'default' : 'secondary'}>
                            {analysisData.voice_analysis.speaking ? 'Speaking' : 'Silent'}
                          </Badge>
                        </div>
                        {analysisData.voice_analysis.confidence !== undefined && (
                          <div className="flex items-center justify-between">
                            <span className="text-xs">Voice Confidence:</span>
                            <span className="text-xs text-muted-foreground">
                              {Math.round(analysisData.voice_analysis.confidence * 100)}%
                            </span>
                          </div>
                        )}
                        {analysisData.voice_analysis.nervousness !== undefined && (
                          <div className="flex items-center justify-between">
                            <span className="text-xs">Nervousness:</span>
                            <span className="text-xs text-muted-foreground">
                              {Math.round(analysisData.voice_analysis.nervousness * 100)}%
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Recommendations */}
                  {analysisData.recommendations && analysisData.recommendations.length > 0 && (
                    <div className="mt-3">
                      <h4 className="text-sm font-medium mb-2">Recommendations:</h4>
                      <ul className="text-xs text-muted-foreground space-y-1">
                        {analysisData.recommendations.map((rec, index) => (
                          <li key={index} className="flex items-start gap-1">
                            <span className="text-blue-500">•</span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Suspicious Behavior */}
                  {analysisData.suspicious_behavior && analysisData.suspicious_behavior.length > 0 && (
                    <div className="mt-3">
                      <h4 className="text-sm font-medium mb-2 text-red-600">⚠️ Suspicious Behavior:</h4>
                      <ul className="text-xs text-red-600 space-y-1">
                        {analysisData.suspicious_behavior.map((behavior, index) => (
                          <li key={index} className="flex items-start gap-1">
                            <span className="text-red-500">⚠</span>
                            {behavior}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* No Analysis Data */}
              {!videoFrame && !error && (
                <div className="text-center py-8 text-muted-foreground">
                  <Camera size={32} className="mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Waiting for video stream...</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
}); 