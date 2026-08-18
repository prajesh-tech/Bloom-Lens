import React from 'react';
import { Card } from '../common/Card';
import { BrainCircuit, Award, FileCheck2, AlertTriangle } from 'lucide-react';
import { QuestionPaper } from '../../types/paper';

interface SummaryCardsProps {
  paper: QuestionPaper;
  questionCount: number;
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({ paper, questionCount }) => {
  const valMeta = paper.validation_metadata;
  const isMismatch = paper.validation_status === 'MISMATCH' || paper.validation_status === 'UNCERTAIN';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Card 1: Total Questions */}
      <Card className="space-y-2">
        <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Total Questions</span>
          <div className="w-8 h-8 rounded-lg bg-sky-50 dark:bg-sky-950/60 border border-sky-200/60 dark:border-sky-800/80 flex items-center justify-center">
            <FileCheck2 className="w-4 h-4 text-sky-600 dark:text-sky-400" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">{questionCount}</span>
          <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">extracted</span>
        </div>
      </Card>

      {/* Card 2: Maximum Paper Marks */}
      <Card className="space-y-2">
        <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Total Paper Marks</span>
          <div className="w-8 h-8 rounded-lg bg-purple-50 dark:bg-purple-950/60 border border-purple-200/60 dark:border-purple-800/80 flex items-center justify-center">
            <Award className="w-4 h-4 text-purple-600 dark:text-purple-400" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">{paper.maximum_marks}</span>
          <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">marks</span>
        </div>
      </Card>

      {/* Card 3: Mark Validation Status */}
      <Card className="space-y-2">
        <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Marks Validation</span>
          {isMismatch ? (
            <div className="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-950/60 border border-amber-200/60 dark:border-amber-800/80 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200/60 dark:border-emerald-800/80 flex items-center justify-center">
              <FileCheck2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-sm font-bold font-mono px-2 py-0.5 rounded ${
              isMismatch ? 'bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800' : 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
            }`}
          >
            {paper.validation_status}
          </span>
          {valMeta?.extracted_marks !== undefined && (
            <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
              ({valMeta.extracted_marks}/{paper.maximum_marks})
            </span>
          )}
        </div>
      </Card>

      {/* Card 4: Subject Code & Exam */}
      <Card className="space-y-2">
        <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Examination</span>
          <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200/60 dark:border-indigo-800/80 flex items-center justify-center">
            <BrainCircuit className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
          </div>
        </div>
        <div>
          <div className="text-base font-bold font-mono text-slate-900 dark:text-white truncate">
            {paper.subject_code}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{paper.examination_type}</p>
        </div>
      </Card>
    </div>
  );
};
