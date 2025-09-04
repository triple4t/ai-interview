"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Building, ArrowLeft, FileText } from "@phosphor-icons/react";
import { useUser } from "@/lib/user-context";
import { JobRecommendations } from "@/components/jobs/job-recommendations";

export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  salary: string;
  match: number;
  description: string;
  fullAnalysis?: string;
  keyMatches?: string[];
  missingSkills?: string[];
  recommendations?: string;
  jdSource?: string;
}

export default function JobsPage() {
  const router = useRouter();
  const { user, isLoading } = useUser();
  const [jobRecommendations, setJobRecommendations] = useState<Job[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState(true);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }

    // Fetch job recommendations from localStorage or API
    const fetchJobRecommendations = () => {
      try {
        const savedJobs = localStorage.getItem("jobRecommendations");
        if (savedJobs) {
          setJobRecommendations(JSON.parse(savedJobs));
        }
      } catch (error) {
        console.error("Error loading job recommendations:", error);
      } finally {
        setIsLoadingJobs(false);
      }
    };

    fetchJobRecommendations();
  }, [user, isLoading, router]);

  if (isLoading || isLoadingJobs) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading jobs...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect to login
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/resume")}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Back</span>
              </Button>
              <h1 className="text-xl font-semibold flex items-center">
                <Building className="h-5 w-5 mr-2" />
                Recommended Jobs
              </h1>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push("/resume")}
              className="flex items-center space-x-2"
            >
              <FileText className="h-4 w-4" />
              <span>Upload New Resume</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {jobRecommendations.length > 0 ? (
          <JobRecommendations
            jobs={jobRecommendations}
            onJobSelect={async (job) => {
              try {
                // Automatically set the JD file for the LiveKit worker
                if (job.jdSource) {
                  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/interview/select-jd`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                      jd_filename: job.jdSource
                    })
                  });

                  if (!response.ok) {
                    console.warn('Failed to set JD file, but continuing with interview');
                  } else {
                    console.log('Successfully set JD file for interview');
                  }
                }

                // Save selected job to localStorage for the interview page
                localStorage.setItem("selectedJob", JSON.stringify(job));
                // Navigate to interview page
                router.push("/interview");
              } catch (error) {
                console.error('Error setting JD file:', error);
                // Continue with interview even if JD setting fails
                localStorage.setItem("selectedJob", JSON.stringify(job));
                router.push("/interview");
              }
            }}
          />
        ) : (
          <div className="text-center py-12">
            <Building className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">
              No job recommendations found
            </h3>
            <p className="text-muted-foreground mb-6">
              Upload your resume to get personalized job recommendations.
            </p>
            <Button onClick={() => router.push("/resume")}>
              Upload Resume
            </Button>
          </div>
        )}
      </main>
    </div>
  );
}
