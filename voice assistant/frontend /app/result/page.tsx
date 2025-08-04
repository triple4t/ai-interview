'use client';

import { useEffect, useState } from 'react';

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
    created_at: string;
    updated_at: string;
}

export default function ResultPage() {
    const [result, setResult] = useState<InterviewResult | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Try to get result from localStorage first (from current interview)
        const storedResult = localStorage.getItem('interviewResult');
        if (storedResult) {
            try {
                const parsedResult = JSON.parse(storedResult);
                setResult(parsedResult);
                setLoading(false);
                // Clear from localStorage after reading
                localStorage.removeItem('interviewResult');
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
                                    <p className="text-muted-foreground">{feedback.feedback}</p>
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