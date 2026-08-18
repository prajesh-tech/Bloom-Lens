import React from 'react';
import { QuestionAnalysis } from '../../types/question';
import { BloomBadge } from '../common/BloomBadge';
import { Badge } from '../common/Badge';
import { formatMarks, formatConfidence, formatQuestionId } from '../../utils/formatters';
import { AlertTriangle, ChevronRight, HelpCircle } from 'lucide-react';

interface QuestionTableProps {
  questions: QuestionAnalysis[];
  selectedQuestionId: number | null;
  onSelectQuestion: (question: QuestionAnalysis) => void;
}

export const QuestionTable: React.FC<QuestionTableProps> = ({
  questions,
  selectedQuestionId,
  onSelectQuestion,
}) => {
  if (questions.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-12 text-center text-slate-500 dark:text-slate-400 space-y-3 transition-colors">
        <HelpCircle className="w-10 h-10 mx-auto text-slate-300 dark:text-slate-600" />
        <h4 className="text-base font-bold text-slate-800 dark:text-slate-200">No Questions Match Filter Criteria</h4>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
          Try resetting your search query or adjusting the Bloom taxonomy level filters.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl overflow-hidden shadow-xs transition-colors">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              <th className="py-3.5 px-4 w-24">ID</th>
              <th className="py-3.5 px-4">Question Text</th>
              <th className="py-3.5 px-4 w-28">Marks</th>
              <th className="py-3.5 px-4 w-44">Bloom Level</th>
              <th className="py-3.5 px-4 w-32">Confidence</th>
              <th className="py-3.5 px-4 w-36">Status</th>
              <th className="py-3.5 px-4 w-12 text-right"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200/80 dark:divide-slate-800 text-sm">
            {questions.map((q) => {
              const isSelected = selectedQuestionId === q.id;
              const bloomLvl = q.effective_bloom_level || q.ai_bloom_level;
              const isLowConfidence = q.bloom_confidence !== null && q.bloom_confidence !== undefined && q.bloom_confidence < 0.70;
              const isUnparsed = q.original_text.includes('[Unparsed section]') || (q.extraction_confidence && q.extraction_confidence < 0.50);

              return (
                <tr
                  key={q.id}
                  onClick={() => onSelectQuestion(q)}
                  className={`group cursor-pointer transition-colors ${
                    isSelected ? 'bg-slate-100/90 dark:bg-slate-800' : 'hover:bg-slate-50/80 dark:hover:bg-slate-800/40'
                  }`}
                >
                  {/* Question ID (JetBrains Mono) */}
                  <td className="py-4 px-4 font-mono font-bold text-xs text-slate-900 dark:text-white whitespace-nowrap">
                    {formatQuestionId(q.question_number)}
                  </td>

                  {/* Question Text */}
                  <td className="py-4 px-4">
                    <div className="space-y-1">
                      <p className="text-slate-900 dark:text-slate-100 font-medium line-clamp-2 leading-relaxed">
                        {q.original_text}
                      </p>
                      {isUnparsed && (
                        <div className="inline-flex items-center gap-1 text-[11px] font-mono text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-800">
                          <AlertTriangle className="w-3 h-3 text-amber-500" />
                          <span>Extraction Warning: Partial OCR text</span>
                        </div>
                      )}
                    </div>
                  </td>

                  {/* Marks (JetBrains Mono) */}
                  <td className="py-4 px-4 font-mono text-xs font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap">
                    {formatMarks(q.marks)}
                  </td>

                  {/* Bloom Level Badge */}
                  <td className="py-4 px-4 whitespace-nowrap">
                    <BloomBadge level={bloomLvl} size="sm" />
                  </td>

                  {/* Confidence (JetBrains Mono & Low Confidence Warning) */}
                  <td className="py-4 px-4 whitespace-nowrap">
                    {isLowConfidence ? (
                      <span className="inline-flex items-center gap-1 font-mono text-xs font-semibold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-800">
                        <AlertTriangle className="w-3 h-3 text-amber-500" />
                        <span>{formatConfidence(q.bloom_confidence)}</span>
                      </span>
                    ) : (
                      <span className="font-mono text-xs text-slate-700 dark:text-slate-300 font-semibold">
                        {formatConfidence(q.bloom_confidence)}
                      </span>
                    )}
                  </td>

                  {/* Review Status */}
                  <td className="py-4 px-4 whitespace-nowrap">
                    {q.review_status === 'CORRECTED' ? (
                      <Badge variant="primary" size="sm" className="font-mono">
                        Corrected
                      </Badge>
                    ) : isUnparsed ? (
                      <Badge variant="warning" size="sm" className="font-mono">
                        Unparsed
                      </Badge>
                    ) : (
                      <Badge variant="outline" size="sm" className="font-mono">
                        Auto-Classified
                      </Badge>
                    )}
                  </td>

                  {/* Action Chevron */}
                  <td className="py-4 px-4 text-right">
                    <ChevronRight className="w-4 h-4 text-slate-400 dark:text-slate-500 group-hover:text-slate-700 dark:group-hover:text-slate-200 group-hover:translate-x-0.5 transition-all" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
