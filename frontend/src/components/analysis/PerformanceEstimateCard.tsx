import React from 'react';
import { Card } from '../common/Card';
import { Skeleton } from '../common/Skeleton';
import { TrendingUp, Award, Info, AlertCircle } from 'lucide-react';
import { usePerformanceEstimateQuery } from '../../services/queries';
import { PerformanceEstimate } from '../../types/paper';

interface PerformanceEstimateCardProps {
  paperId: number;
  maxMarks?: number;
  estimate?: PerformanceEstimate | null;
  isLoading?: boolean;
  isError?: boolean;
}

const REASON_LABELS: Record<string, string> = {
  no_valid_questions: 'No valid questions with confirmed marks and Bloom levels remain.',
  invalid_max_marks: 'Paper maximum marks is invalid or missing.',
  too_many_excluded: 'Questions with missing marks or Bloom levels exceed the allowed 20% threshold.',
  paper_not_completed: 'Question paper analysis is still in progress.',
};

export const PerformanceEstimateCard: React.FC<PerformanceEstimateCardProps> = ({
  paperId,
  maxMarks,
  estimate: propEstimate,
  isLoading: propIsLoading,
  isError: propIsError,
}) => {
  // Use hook if props are not explicitly provided
  const query = usePerformanceEstimateQuery(paperId);
  const isLoading = propIsLoading !== undefined ? propIsLoading : query.isLoading;
  const isError = propIsError !== undefined ? propIsError : query.isError;
  const estimate = propEstimate !== undefined ? propEstimate : query.data;

  const disclaimerText =
    "Heuristic estimate based solely on this paper's Bloom's Taxonomy and marks distribution. Not actual student performance.";

  if (isLoading) {
    return (
      <Card className="space-y-4 border-slate-200/80 dark:border-slate-800" data-testid="performance-estimate-loading">
        <div className="flex items-center justify-between">
          <Skeleton className="h-5 w-56" />
          <Skeleton className="h-4 w-24" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
        <Skeleton className="h-4 w-full" />
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className="space-y-3 border-amber-200/60 dark:border-amber-900/40 bg-amber-50/30 dark:bg-amber-950/20" data-testid="performance-estimate-error">
        <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <h4 className="text-sm font-bold">Estimated Student Performance</h4>
        </div>
        <p className="text-xs text-amber-800 dark:text-amber-300 font-mono">
          Unable to calculate performance estimate at this time.
        </p>
      </Card>
    );
  }

  const isUnavailable =
    !estimate ||
    estimate.estimated_pass_percentage === null ||
    estimate.estimated_average_marks === null;

  if (isUnavailable) {
    const reasonCode = estimate?.reason || 'unavailable';
    const reasonMessage = REASON_LABELS[reasonCode] || `Estimate is currently unavailable (${reasonCode}).`;

    return (
      <Card className="space-y-3 border-slate-200/80 dark:border-slate-800" data-testid="performance-estimate-unavailable">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-slate-900 dark:text-white">Estimated Student Performance</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              Unavailable
            </span>
          </div>
        </div>
        <p className="text-xs text-slate-600 dark:text-slate-400 font-mono">
          {reasonMessage}
        </p>
        <div className="flex items-start gap-1.5 pt-1 border-t border-slate-100 dark:border-slate-800 text-slate-500 dark:text-slate-400 text-xs">
          <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>{disclaimerText}</span>
        </div>
      </Card>
    );
  }

  const passPct = estimate.estimated_pass_percentage;
  const avgMarks = estimate.estimated_average_marks;

  return (
    <Card className="space-y-4 border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs" data-testid="performance-estimate-card">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Estimated Student Performance</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
            Cognitive difficulty projection from marks-weighted Bloom distribution
          </p>
        </div>
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium font-mono bg-sky-50 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 border border-sky-200/60 dark:border-sky-800/80">
          Heuristic Model
        </span>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Metric 1: Estimated Pass Percentage */}
        <div className="p-4 rounded-lg bg-slate-50/70 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Estimated Pass Percentage</span>
            <div className="w-7 h-7 rounded-md bg-teal-50 dark:bg-teal-950/60 border border-teal-200/60 dark:border-teal-800/80 flex items-center justify-center">
              <TrendingUp className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5 pt-1">
            <span className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white" data-testid="estimated-pass-pct">
              {passPct}%
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Estimated</span>
          </div>
        </div>

        {/* Metric 2: Estimated Average Marks */}
        <div className="p-4 rounded-lg bg-slate-50/70 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Estimated Average Marks</span>
            <div className="w-7 h-7 rounded-md bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200/60 dark:border-indigo-800/80 flex items-center justify-center">
              <Award className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
            </div>
          </div>
          <div className="flex items-baseline gap-1.5 pt-1">
            <span className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white" data-testid="estimated-avg-marks">
              {avgMarks}
              {maxMarks !== undefined && (
                <span className="text-base font-normal text-slate-500 dark:text-slate-400"> / {maxMarks}</span>
              )}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Estimated</span>
          </div>
        </div>
      </div>

      {/* Neutral Note */}
      <div className="flex items-start gap-2 pt-2 border-t border-slate-100 dark:border-slate-800/80 text-slate-500 dark:text-slate-400 text-xs">
        <Info className="w-3.5 h-3.5 mt-0.5 shrink-0 text-slate-400 dark:text-slate-500" />
        <span className="leading-relaxed">{disclaimerText}</span>
      </div>
    </Card>
  );
};
