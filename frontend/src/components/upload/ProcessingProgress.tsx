import React from 'react';
import { Loader2, CheckCircle2, FileText, BrainCircuit, BarChart3 } from 'lucide-react';

interface ProcessingProgressProps {
  currentStep: number; // 1: Uploading, 2: Extracting, 3: Analyzing, 4: Generating
}

export const ProcessingProgress: React.FC<ProcessingProgressProps> = ({ currentStep }) => {
  const steps = [
    { number: 1, label: 'Uploading Document', icon: FileText },
    { number: 2, label: 'Extracting Questions', icon: FileText },
    { number: 3, label: 'Analyzing Cognitive Bloom Levels', icon: BrainCircuit },
    { number: 4, label: 'Generating Analytics Report', icon: BarChart3 },
  ];

  const progressPct = (currentStep / steps.length) * 100;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-8 shadow-sm space-y-6 max-w-xl mx-auto transition-colors">
      <div className="text-center space-y-2">
        <div className="w-12 h-12 mx-auto rounded-xl bg-slate-900 dark:bg-sky-950 text-white flex items-center justify-center shadow-xs">
          <Loader2 className="w-6 h-6 animate-spin text-sky-400" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">Analyzing Question Paper</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
          Please wait while BloomLens processes your document...
        </p>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-100 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden">
        <div
          className="bg-slate-900 dark:bg-sky-500 h-full transition-all duration-500 ease-out"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Steps List */}
      <div className="space-y-3 pt-2">
        {steps.map((step) => {
          const isDone = currentStep > step.number;
          const isCurrent = currentStep === step.number;

          return (
            <div
              key={step.number}
              className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
                isCurrent
                  ? 'bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 font-medium text-slate-900 dark:text-white shadow-xs'
                  : isDone
                  ? 'bg-emerald-50/50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300'
                  : 'bg-transparent border-transparent text-slate-400 dark:text-slate-500'
              }`}
            >
              {isDone ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-5 h-5 text-slate-900 dark:text-white animate-spin flex-shrink-0" />
              ) : (
                <step.icon className="w-5 h-5 text-slate-300 dark:text-slate-600 flex-shrink-0" />
              )}
              <span className="text-sm">{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
