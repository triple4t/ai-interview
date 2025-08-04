'use client';

import { useState, useRef } from 'react';
import { motion } from 'motion/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, FileText, CheckCircle, Warning, MagnifyingGlass } from '@phosphor-icons/react';
import { apiClient } from '@/lib/api';

interface ResumeUploadProps {
    onResumeUploaded: (resumeData: any) => void;
    onJobRecommendations: (jobs: any[]) => void;
}

interface JobMatch {
    jd_title?: string;
    jd_source?: string;
    match_percentage?: number;
    analysis?: string;
    key_matches?: string[];
    missing_skills?: string[];
    recommendations?: string;
    error?: string;
}

export const ResumeUpload = ({ onResumeUploaded, onJobRecommendations }: ResumeUploadProps) => {
    const [isUploading, setIsUploading] = useState(false);
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Validate file type - only PDF for now
            if (file.type !== 'application/pdf') {
                setErrorMessage('Please upload a PDF file');
                setUploadStatus('error');
                return;
            }

            // Validate file size (10MB limit)
            if (file.size > 10 * 1024 * 1024) {
                setErrorMessage('File size must be less than 10MB');
                setUploadStatus('error');
                return;
            }

            setUploadedFile(file);
            setUploadStatus('idle');
            setErrorMessage('');
        }
    };

    const uploadResume = async (file: File): Promise<any> => {
        return await apiClient.uploadResume(file);
    };

    const getJobMatches = async (): Promise<JobMatch[]> => {
        const data = await apiClient.getJobMatches(0.65);
        return data.matches || [];
    };

    const handleUpload = async () => {
        if (!uploadedFile) return;

        setIsUploading(true);
        setUploadStatus('idle');
        setErrorMessage('');

        try {
            // Step 1: Upload resume
            console.log('Uploading resume...');
            const uploadResult = await uploadResume(uploadedFile);
            console.log('Upload result:', uploadResult);

            setUploadStatus('success');

            // Step 2: Analyze and get job matches
            setIsAnalyzing(true);
            console.log('Analyzing resume and getting job matches...');

            const jobMatches = await getJobMatches();
            console.log('Job matches:', jobMatches);

            // Check if we got an error response
            if (jobMatches.length === 1 && jobMatches[0].error) {
                throw new Error(jobMatches[0].error);
            }

            // Transform job matches to the expected format
            const transformedJobs = jobMatches.map((match, index) => ({
                id: index + 1,
                title: match.jd_title || 'Unknown Position',
                company: 'AI Interview Assistant',
                location: 'Remote/Hybrid',
                salary: 'Competitive',
                match: Math.round((match.match_percentage || 0) * 100),
                description: match.analysis ? (match.analysis.length > 200 ? match.analysis.substring(0, 200) + '...' : match.analysis) : 'No analysis available',
                fullAnalysis: match.analysis || 'No detailed analysis available',
                keyMatches: match.key_matches || [],
                missingSkills: match.missing_skills || [],
                recommendations: match.recommendations || 'No recommendations available',
                jdSource: match.jd_source || 'Unknown'
            }));

            // Create mock resume data (since we don't extract it from PDF yet)
            const mockResumeData = {
                name: 'Resume Analysis Complete',
                email: 'analysis@aiinterview.com',
                skills: jobMatches.length > 0 ? jobMatches[0].key_matches : [],
                experience: 'Analyzed from resume',
                education: 'Analyzed from resume'
            };

            onResumeUploaded(mockResumeData);
            onJobRecommendations(transformedJobs);

            setIsAnalyzing(false);

        } catch (error) {
            console.error('Error during upload/analysis:', error);
            setErrorMessage(error instanceof Error ? error.message : 'Failed to upload resume. Please try again.');
            setUploadStatus('error');
            setIsAnalyzing(false);
        } finally {
            setIsUploading(false);
        }
    };

    const handleDrop = (event: React.DragEvent) => {
        event.preventDefault();
        const file = event.dataTransfer.files[0];
        if (file) {
            const input = fileInputRef.current;
            if (input) {
                input.files = event.dataTransfer.files;
                handleFileSelect({ target: { files: event.dataTransfer.files } } as any);
            }
        }
    };

    const handleDragOver = (event: React.DragEvent) => {
        event.preventDefault();
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-2xl mx-auto"
        >
            <Card className="w-full">
                <CardHeader className="text-center">
                    <CardTitle className="text-2xl">Upload Your Resume</CardTitle>
                    <CardDescription>
                        Upload your resume to get personalized job recommendations using AI analysis
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div
                        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${uploadedFile ? 'border-green-500 bg-green-50' : 'border-gray-300 hover:border-gray-400'
                            }`}
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".pdf"
                            onChange={handleFileSelect}
                            className="hidden"
                        />

                        {!uploadedFile ? (
                            <div className="space-y-4">
                                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                                <div>
                                    <p className="text-lg font-medium">Drop your resume here</p>
                                    <p className="text-sm text-gray-500">or click to browse (PDF only)</p>
                                </div>
                                <Button
                                    variant="outline"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    Choose File
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
                                <div>
                                    <p className="text-lg font-medium text-green-700">{uploadedFile.name}</p>
                                    <p className="text-sm text-green-600">File selected successfully</p>
                                </div>
                                <Button
                                    variant="outline"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    Choose Different File
                                </Button>
                            </div>
                        )}
                    </div>

                    {errorMessage && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg"
                        >
                            <Warning className="h-5 w-5 text-red-500" />
                            <span className="text-red-700 text-sm">{errorMessage}</span>
                        </motion.div>
                    )}

                    {uploadStatus === 'success' && !isAnalyzing && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex items-center space-x-2 p-3 bg-green-50 border border-green-200 rounded-lg"
                        >
                            <CheckCircle className="h-5 w-5 text-green-500" />
                            <span className="text-green-700 text-sm">Resume uploaded successfully!</span>
                        </motion.div>
                    )}

                    {isAnalyzing && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex items-center space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-lg"
                        >
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                            <span className="text-blue-700 text-sm">Analyzing resume and finding job matches...</span>
                        </motion.div>
                    )}

                    <Button
                        onClick={handleUpload}
                        disabled={!uploadedFile || isUploading || isAnalyzing}
                        className="w-full"
                        size="lg"
                    >
                        {isUploading || isAnalyzing ? (
                            <div className="flex items-center space-x-2">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                <span>
                                    {isUploading ? 'Uploading...' : 'Analyzing & Finding Matches...'}
                                </span>
                            </div>
                        ) : (
                            <div className="flex items-center space-x-2">
                                <MagnifyingGlass className="h-5 w-5" />
                                <span>Upload Resume & Get AI Recommendations</span>
                            </div>
                        )}
                    </Button>
                </CardContent>
            </Card>
        </motion.div>
    );
}; 