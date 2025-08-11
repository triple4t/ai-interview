"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Building,
  MapPin,
  CurrencyDollar,
  Star,
  CheckCircle,
  XCircle,
  Lightbulb,
  CaretDown,
  CaretUp,
  FileText,
} from "@phosphor-icons/react";

interface JobRecommendation {
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

interface JobRecommendationsProps {
  jobs: JobRecommendation[];
  onJobSelect?: (job: JobRecommendation) => void;
}

export const JobRecommendations = ({
  jobs,
  onJobSelect,
}: JobRecommendationsProps) => {
  const [expandedJob, setExpandedJob] = useState<number | null>(null);

  const toggleExpanded = (jobId: number) => {
    setExpandedJob(expandedJob === jobId ? null : jobId);
  };

  const getMatchColor = (match: number) => {
    if (match >= 80) return "bg-green-100 text-green-800 border-green-200";
    if (match >= 60) return "bg-yellow-100 text-yellow-800 border-yellow-200";
    return "bg-red-100 text-red-800 border-red-200";
  };

  const getMatchIcon = (match: number) => {
    if (match >= 80) return <CheckCircle className="h-4 w-4" />;
    if (match >= 60) return <Star className="h-4 w-4" />;
    return <XCircle className="h-4 w-4" />;
  };

  if (jobs.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-4xl mx-auto"
      >
        <Card className="w-full">
          <CardContent className="p-8 text-center">
            <div className="space-y-4">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="text-lg font-medium text-gray-900">
                No Job Matches Found
              </h3>
              <p className="text-gray-500">
                We couldn't find any job descriptions that match your resume
                with 65% or higher compatibility. Try uploading a different
                resume or check back later for new opportunities.
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-4xl mx-auto space-y-6"
    >
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          AI-Powered Job Recommendations
        </h2>
        <p className="text-gray-600">
          Found {jobs.length} job(s) that match your resume with 65%+
          compatibility
        </p>
      </div>

      <div className="grid gap-6">
        {jobs.map((job, index) => (
          <motion.div
            key={job.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
          >
            <Card className="w-full hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <CardTitle className="text-xl">{job.title}</CardTitle>
                      <Badge
                        className={`${getMatchColor(job.match)} flex items-center gap-1`}
                      >
                        {getMatchIcon(job.match)}
                        {job.match}% Match
                      </Badge>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <Building className="h-4 w-4" />
                        <span>{job.company}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        <span>{job.location}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <CurrencyDollar className="h-4 w-4" />
                        <span>{job.salary}</span>
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleExpanded(job.id)}
                    className="ml-4"
                  >
                    {expandedJob === job.id ? (
                      <CaretUp className="h-4 w-4" />
                    ) : (
                      <CaretDown className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                <p className="text-gray-700">{job.description}</p>

                {expandedJob === job.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="space-y-6 pt-4 border-t"
                  >
                    {/* AI Analysis */}
                    {job.fullAnalysis && (
                      <div className="space-y-3">
                        <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                          <Lightbulb className="h-4 w-4" />
                          AI Analysis
                        </h4>
                        <div className="bg-blue-50 p-4 rounded-lg">
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">
                            {job.fullAnalysis}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Key Matches */}
                    {job.keyMatches && job.keyMatches.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-green-600" />
                          Key Matches
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {job.keyMatches.map((skill, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className="bg-green-100 text-green-800"
                            >
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Missing Skills */}
                    {job.missingSkills && job.missingSkills.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                          <XCircle className="h-4 w-4 text-red-600" />
                          Skills to Develop
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {job.missingSkills.map((skill, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="border-red-200 text-red-700"
                            >
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {job.recommendations && (
                      <div className="space-y-3">
                        <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                          <Lightbulb className="h-4 w-4 text-yellow-600" />
                          Recommendations
                        </h4>
                        <div className="bg-yellow-50 p-4 rounded-lg">
                          <p className="text-sm text-gray-700">
                            {job.recommendations}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-4">
                      <Button
                        onClick={() => onJobSelect?.(job)}
                        className="flex-1"
                      >
                        Start AI Interview
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() =>
                          window.open(
                            `/api/v1/resume/jd/${job.jdSource}`,
                            "_blank",
                          )
                        }
                      >
                        View Full JD
                      </Button>
                    </div>
                  </motion.div>
                )}

                {expandedJob !== job.id && (
                  <div className="flex gap-3">
                    <Button
                      onClick={() => onJobSelect?.(job)}
                      className="flex-1"
                    >
                      Start AI Interview
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => toggleExpanded(job.id)}
                    >
                      View Details
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};
