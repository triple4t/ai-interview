'use client';

import { useEffect, useState } from 'react';

interface FaceAnalysisData {
    emotion?: string;
    eye_state?: string;
    face_detected?: boolean;
    confidence?: number;
    attention_score?: number;
    engagement_level?: string;
    recommendations?: string[];
    suspicious_behavior?: string[];
}

interface InterviewResult {
    session_id: string;
    user_id: number;
    total_score: number;
    max_score: number;
    percentage: number;
    questions_evaluated: number;
    overall_analysis: string;
    detailed_feedback: Array<{
        question: string;
        answer: string;
        score: number;
        feedback: string;
        strengths: string[];
        weaknesses: string[];
    }>;
    strengths: string[];
    areas_for_improvement: string[];
    recommendations: string[];
    transcript?: Array<{
        role: string;
        content: string;
        timestamp?: string;
    }>;
    face_analysis?: {
        face_detected: boolean;
        face_count: number;
        confidence: number;
        attention_score: number;
        engagement_level: string;
        eye_tracking?: {
            eye_state: string;
            eye_tracking: string;
            eye_aspect_ratio: number;
            screen_distance: number;
        };
        head_pose?: {
            looking_at_screen: boolean;
            head_pose: string;
            gaze_distance: number;
        };
        multiple_faces?: {
            face_count: number;
            multiple_faces_detected: boolean;
        };
        screen_sharing?: {
            screen_sharing_detected: boolean;
            time_since_last_activity: number;
        };
        suspicious_behavior: string[];
        recommendations: string[];
    };
    voice_analysis?: {
        speaking: boolean;
        confidence: number;
        nervousness: number;
        speech_patterns: string[];
    };
    created_at: string;
    updated_at: string;
}

export default function ResultPage() {
    const [result, setResult] = useState<InterviewResult | null>(null);
    const [faceAnalysisData, setFaceAnalysisData] = useState<FaceAnalysisData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Try to get result from localStorage first (from current interview)
        const storedResult = localStorage.getItem('interviewResult');
        const storedFaceAnalysis = localStorage.getItem('faceAnalysisData');

        if (storedResult) {
            try {
                const parsedResult = JSON.parse(storedResult);
                setResult(parsedResult);

                // Parse face analysis data if available
                if (storedFaceAnalysis) {
                    try {
                        const parsedFaceAnalysis = JSON.parse(storedFaceAnalysis);
                        setFaceAnalysisData(parsedFaceAnalysis);
                    } catch (e) {
                        console.error('Error parsing face analysis data:', e);
                    }
                }

                setLoading(false);
                // Clear from localStorage after reading
                localStorage.removeItem('interviewResult');
                localStorage.removeItem('faceAnalysisData');
                return;
            } catch (e) {
                console.error('Error parsing stored result:', e);
            }
        }

        // Fallback: fetch from API
        async function fetchLatestResult() {
            setLoading(true);
            try {
                const res = await fetch('http://localhost:8000/api/v1/interview/history', { credentials: 'include' });
                if (res.ok) {
                    const data: InterviewResult[] = await res.json();
                    if (data.length > 0) {
                        setResult(data[0]); // Get the most recent result
                    }
                }
            } catch (e) {
                console.error('Error fetching result:', e);
            }
            setLoading(false);
        }
        fetchLatestResult();
    }, []);

    const getScoreColor = (percentage: number) => {
        if (percentage >= 80) return 'text-green-600';
        if (percentage >= 60) return 'text-yellow-600';
        return 'text-red-600';
    };

    const getScoreLabel = (percentage: number) => {
        if (percentage >= 90) return 'Exceptional';
        if (percentage >= 80) return 'Excellent';
        if (percentage >= 70) return 'Good';
        if (percentage >= 60) return 'Satisfactory';
        if (percentage >= 50) return 'Needs Improvement';
        return 'Poor';
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex flex-col items-center justify-center p-8">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-muted-foreground">Analyzing your interview...</p>
                </div>
            </div>
        );
    }

    if (!result) {
        return (
            <div className="min-h-screen bg-background flex flex-col items-center justify-center p-8">
                <div className="w-full max-w-2xl bg-card rounded-lg shadow-lg p-8 text-center">
                    <h1 className="text-3xl font-bold mb-4">No Interview Results</h1>
                    <p className="text-muted-foreground mb-6">
                        No interview results found. Please complete an interview first.
                    </p>
                    <a
                        href="/interview"
                        className="bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:bg-primary/90 transition-colors"
                    >
                        Start Interview
                    </a>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                {/* Header */}
                <div className="bg-card rounded-lg shadow-lg p-8 text-center">
                    <h1 className="text-4xl font-bold mb-4">Interview Results</h1>
                    <div className="flex items-center justify-center space-x-4 mb-6">
                        <div className={`text-6xl font-bold ${getScoreColor(result.percentage)}`}>
                            {result.total_score}/{result.max_score}
                        </div>
                        <div className="text-left">
                            <div className={`text-2xl font-semibold ${getScoreColor(result.percentage)}`}>
                                {result.percentage.toFixed(1)}%
                            </div>
                            <div className="text-lg text-muted-foreground">
                                {getScoreLabel(result.percentage)}
                            </div>
                        </div>
                    </div>
                    <p className="text-muted-foreground">
                        {result.questions_evaluated} questions evaluated
                    </p>
                </div>

                {/* Overall Analysis */}
                <div className="bg-card rounded-lg shadow-lg p-8">
                    <h2 className="text-2xl font-bold mb-4">Overall Analysis</h2>
                    <p className="text-lg leading-relaxed">{result.overall_analysis}</p>
                </div>

                {/* Strengths and Areas for Improvement */}
                <div className="grid md:grid-cols-2 gap-8">
                    <div className="bg-card rounded-lg shadow-lg p-8">
                        <h2 className="text-2xl font-bold mb-4 text-green-600">Strengths</h2>
                        <ul className="space-y-2">
                            {result.strengths.map((strength, idx) => (
                                <li key={idx} className="flex items-start">
                                    <span className="text-green-500 mr-2">✓</span>
                                    <span>{strength}</span>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className="bg-card rounded-lg shadow-lg p-8">
                        <h2 className="text-2xl font-bold mb-4 text-orange-600">Areas for Improvement</h2>
                        <ul className="space-y-2">
                            {result.areas_for_improvement.map((area, idx) => (
                                <li key={idx} className="flex items-start">
                                    <span className="text-orange-500 mr-2">•</span>
                                    <span>{area}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Detailed Feedback */}
                <div className="bg-card rounded-lg shadow-lg p-8">
                    <h2 className="text-2xl font-bold mb-6">Detailed Feedback</h2>
                    <div className="space-y-6">
                        {result.detailed_feedback.map((feedback, idx) => (
                            <div key={idx} className="border rounded-lg p-6">
                                <div className="flex justify-between items-start mb-4">
                                    <h3 className="text-lg font-semibold">Question {idx + 1}</h3>
                                    <div className={`text-lg font-bold ${getScoreColor((feedback.score / 100) * 100)}`}>
                                        {feedback.score}/100
                                    </div>
                                </div>

                                <div className="mb-4">
                                    <p className="font-medium mb-2">Question:</p>
                                    <p className="text-muted-foreground mb-4">{feedback.question}</p>

                                    <p className="font-medium mb-2">Your Answer:</p>
                                    <p className="text-muted-foreground mb-4">{feedback.answer}</p>

                                    <p className="font-medium mb-2">Feedback:</p>
                                    <p className="text-muted-foreground mb-4">{feedback.feedback}</p>

                                    {/* Show conversation transcript for this question */}
                                    {result.transcript && (
                                        <div className="mt-4">
                                            <p className="font-medium mb-2">Conversation:</p>
                                            <div className="space-y-2 max-h-48 overflow-y-auto bg-gray-50 rounded-lg p-3">
                                                {result.transcript.map((message, msgIdx) => {
                                                    // Check if this message is related to the current question
                                                    const messageContent = message.content.toLowerCase();
                                                    const questionContent = feedback.question.toLowerCase();

                                                    // Show messages that contain the question or are user responses
                                                    const isRelevant = messageContent.includes(questionContent.substring(0, 20)) ||
                                                        (message.role === 'user' && msgIdx > 0);

                                                    if (isRelevant) {
                                                        return (
                                                            <div key={msgIdx} className={`p-2 rounded text-sm ${message.role === 'user'
                                                                ? 'bg-blue-100 border-l-2 border-blue-400'
                                                                : 'bg-gray-100 border-l-2 border-gray-400'
                                                                }`}>
                                                                <div className="flex items-start justify-between">
                                                                    <div className="flex-1">
                                                                        <div className="font-medium text-xs mb-1">
                                                                            {message.role === 'user' ? 'You' : 'Interviewer'}
                                                                        </div>
                                                                        <div className="text-xs text-gray-700">
                                                                            {message.content}
                                                                        </div>
                                                                    </div>
                                                                    {message.timestamp && (
                                                                        <div className="text-xs text-gray-500 ml-2">
                                                                            {new Date(message.timestamp).toLocaleTimeString()}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        );
                                                    }
                                                    return null;
                                                })}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <div>
                                        <h4 className="font-medium text-green-600 mb-2">Strengths:</h4>
                                        <ul className="space-y-1">
                                            {feedback.strengths.map((strength, sIdx) => (
                                                <li key={sIdx} className="text-sm text-muted-foreground">
                                                    • {strength}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-orange-600 mb-2">Weaknesses:</h4>
                                        <ul className="space-y-1">
                                            {feedback.weaknesses.map((weakness, wIdx) => (
                                                <li key={wIdx} className="text-sm text-muted-foreground">
                                                    • {weakness}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>



                {/* Enhanced Face Analysis Results */}
                {result.face_analysis && (
                    <div className="bg-card rounded-lg shadow-lg p-8">
                        <h2 className="text-2xl font-bold mb-6">Enhanced Face Analysis Results</h2>
                        <div className="grid md:grid-cols-2 gap-6">
                            {/* Basic Face Detection */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold">Face Detection</h3>
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <span className="font-medium">Face Detected:</span>
                                        <span className={result.face_analysis.face_detected ? 'text-green-600' : 'text-red-600'}>
                                            {result.face_analysis.face_detected ? 'Yes' : 'No'}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="font-medium">Face Count:</span>
                                        <span className="text-muted-foreground">
                                            {result.face_analysis.face_count}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="font-medium">Confidence:</span>
                                        <span className="text-muted-foreground">
                                            {Math.round(result.face_analysis.confidence * 100)}%
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Engagement Analysis */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold">Engagement Analysis</h3>
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <span className="font-medium">Engagement Level:</span>
                                        <span className={`font-medium ${result.face_analysis.engagement_level === 'high' ? 'text-green-600' :
                                            result.face_analysis.engagement_level === 'medium' ? 'text-yellow-600' :
                                                'text-red-600'
                                            }`}>
                                            {result.face_analysis.engagement_level.charAt(0).toUpperCase() + result.face_analysis.engagement_level.slice(1)}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="font-medium">Attention Score:</span>
                                        <span className="text-muted-foreground">
                                            {Math.round(result.face_analysis.attention_score * 100)}%
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Eye Tracking */}
                            {result.face_analysis.eye_tracking && (
                                <div className="space-y-4">
                                    <h3 className="text-lg font-semibold">Eye Tracking</h3>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span className="font-medium">Eye State:</span>
                                            <span className={`font-medium ${result.face_analysis.eye_tracking.eye_state === 'open' ? 'text-green-600' :
                                                result.face_analysis.eye_tracking.eye_state === 'closed' ? 'text-red-600' :
                                                    'text-yellow-600'
                                                }`}>
                                                {result.face_analysis.eye_tracking.eye_state.charAt(0).toUpperCase() + result.face_analysis.eye_tracking.eye_state.slice(1)}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="font-medium">Eye Tracking:</span>
                                            <span className={`font-medium ${result.face_analysis.eye_tracking.eye_tracking === 'looking_at_screen' ? 'text-green-600' : 'text-red-600'}`}>
                                                {result.face_analysis.eye_tracking.eye_tracking === 'looking_at_screen' ? 'Looking at Screen' : 'Looking Away'}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="font-medium">Eye Aspect Ratio:</span>
                                            <span className="text-muted-foreground">
                                                {result.face_analysis.eye_tracking.eye_aspect_ratio.toFixed(3)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Head Pose */}
                            {result.face_analysis.head_pose && (
                                <div className="space-y-4">
                                    <h3 className="text-lg font-semibold">Head Pose</h3>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span className="font-medium">Looking at Screen:</span>
                                            <span className={`font-medium ${result.face_analysis.head_pose.looking_at_screen ? 'text-green-600' : 'text-red-600'}`}>
                                                {result.face_analysis.head_pose.looking_at_screen ? 'Yes' : 'No'}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="font-medium">Head Pose:</span>
                                            <span className="text-muted-foreground capitalize">
                                                {result.face_analysis.head_pose.head_pose}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="font-medium">Gaze Distance:</span>
                                            <span className="text-muted-foreground">
                                                {Math.round(result.face_analysis.head_pose.gaze_distance)}px
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Multiple Faces */}
                            {result.face_analysis.multiple_faces && (
                                <div className="space-y-4">
                                    <h3 className="text-lg font-semibold">Multiple Face Detection</h3>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span className="font-medium">Multiple Faces:</span>
                                            <span className={`font-medium ${result.face_analysis.multiple_faces.multiple_faces_detected ? 'text-red-600' : 'text-green-600'}`}>
                                                {result.face_analysis.multiple_faces.multiple_faces_detected ? 'Detected' : 'None'}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="font-medium">Face Count:</span>
                                            <span className="text-muted-foreground">
                                                {result.face_analysis.multiple_faces.face_count}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Screen Sharing */}
                            {result.face_analysis.screen_sharing && (
                                <div className="space-y-4">
                                    <h3 className="text-lg font-semibold">Screen Activity</h3>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span className="font-medium">Screen Switching:</span>
                                            <span className={`font-medium ${result.face_analysis.screen_sharing.screen_sharing_detected ? 'text-red-600' : 'text-green-600'}`}>
                                                {result.face_analysis.screen_sharing.screen_sharing_detected ? 'Detected' : 'None'}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="font-medium">Last Activity:</span>
                                            <span className="text-muted-foreground">
                                                {Math.round(result.face_analysis.screen_sharing.time_since_last_activity)}s ago
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Suspicious Behavior */}
                        {result.face_analysis.suspicious_behavior && result.face_analysis.suspicious_behavior.length > 0 && (
                            <div className="mt-6">
                                <h3 className="text-lg font-semibold text-red-600 mb-3">⚠️ Suspicious Behavior Detected</h3>
                                <ul className="space-y-2">
                                    {result.face_analysis.suspicious_behavior.map((behavior, idx) => (
                                        <li key={idx} className="flex items-start">
                                            <span className="text-red-500 mr-2 mt-1">⚠</span>
                                            <span className="text-sm text-red-600">{behavior}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Recommendations */}
                        {result.face_analysis.recommendations && result.face_analysis.recommendations.length > 0 && (
                            <div className="mt-6">
                                <h3 className="text-lg font-semibold mb-3">Face Analysis Recommendations</h3>
                                <ul className="space-y-2">
                                    {result.face_analysis.recommendations.map((rec, idx) => (
                                        <li key={idx} className="flex items-start">
                                            <span className="text-blue-500 mr-2 mt-1">•</span>
                                            <span className="text-sm">{rec}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}

                {/* Voice Analysis Results */}
                {result.voice_analysis && (
                    <div className="bg-card rounded-lg shadow-lg p-8">
                        <h2 className="text-2xl font-bold mb-6">Voice Analysis Results</h2>
                        <div className="grid md:grid-cols-2 gap-6">
                            {/* Voice Status */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold">Voice Status</h3>
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <span className="font-medium">Speaking:</span>
                                        <span className={`font-medium ${result.voice_analysis.speaking ? 'text-green-600' : 'text-red-600'}`}>
                                            {result.voice_analysis.speaking ? 'Yes' : 'No'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Voice Quality */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold">Voice Quality</h3>
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <span className="font-medium">Confidence:</span>
                                        <span className="text-muted-foreground">
                                            {Math.round(result.voice_analysis.confidence * 100)}%
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="font-medium">Nervousness:</span>
                                        <span className={`font-medium ${result.voice_analysis.nervousness > 0.7 ? 'text-red-600' :
                                            result.voice_analysis.nervousness > 0.4 ? 'text-yellow-600' : 'text-green-600'
                                            }`}>
                                            {Math.round(result.voice_analysis.nervousness * 100)}%
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Speech Patterns */}
                            {result.voice_analysis.speech_patterns && result.voice_analysis.speech_patterns.length > 0 && (
                                <div className="md:col-span-2 space-y-4">
                                    <h3 className="text-lg font-semibold">Speech Patterns</h3>
                                    <ul className="space-y-2">
                                        {result.voice_analysis.speech_patterns.map((pattern, idx) => (
                                            <li key={idx} className="flex items-start">
                                                <span className="text-blue-500 mr-2 mt-1">•</span>
                                                <span className="text-sm">{pattern}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Recommendations */}
                <div className="bg-card rounded-lg shadow-lg p-8">
                    <h2 className="text-2xl font-bold mb-4">Recommendations</h2>
                    <ul className="space-y-3">
                        {result.recommendations.map((recommendation, idx) => (
                            <li key={idx} className="flex items-start">
                                <span className="text-blue-500 mr-3 mt-1">→</span>
                                <span className="text-lg">{recommendation}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Action Buttons */}
                <div className="bg-card rounded-lg shadow-lg p-8 text-center">
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <a
                            href="/interview"
                            className="bg-primary text-primary-foreground px-8 py-3 rounded-lg hover:bg-primary/90 transition-colors"
                        >
                            Practice Again
                        </a>
                        <a
                            href="/resume"
                            className="bg-secondary text-secondary-foreground px-8 py-3 rounded-lg hover:bg-secondary/90 transition-colors"
                        >
                            Upload Resume
                        </a>
                        <a
                            href="/"
                            className="bg-muted text-muted-foreground px-8 py-3 rounded-lg hover:bg-muted/90 transition-colors"
                        >
                            Back to Home
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
} 