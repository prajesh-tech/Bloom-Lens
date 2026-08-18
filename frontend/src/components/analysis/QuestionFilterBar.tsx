import React from 'react';
import { Search, RotateCcw, Filter } from 'lucide-react';
import { BLOOM_CONFIG } from '../../config/bloomConfig';

interface QuestionFilterBarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedBloom: string;
  onBloomChange: (level: string) => void;
  onReset: () => void;
  filteredCount: number;
  totalCount: number;
}

export const QuestionFilterBar: React.FC<QuestionFilterBarProps> = ({
  searchQuery,
  onSearchChange,
  selectedBloom,
  onBloomChange,
  onReset,
  filteredCount,
  totalCount,
}) => {
  const bloomLevels: { label: string; value: string }[] = [
    { label: 'All Levels', value: 'ALL' },
    ...Object.keys(BLOOM_CONFIG).map((lbl) => ({ label: lbl, value: lbl })),
  ];

  const hasActiveFilters = searchQuery !== '' || selectedBloom !== 'ALL';

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-4 shadow-xs space-y-4 transition-colors">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search Field */}
        <div className="relative w-full sm:w-96">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
          <input
            type="text"
            placeholder="Search questions or ID (e.g. Q01, normalization)..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600 focus:bg-white dark:focus:bg-slate-800 transition-all font-sans"
          />
        </div>

        {/* Counter & Reset Action */}
        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end text-xs font-mono text-slate-500 dark:text-slate-400">
          <span>
            Showing <strong className="text-slate-900 dark:text-white">{filteredCount}</strong> of {totalCount} questions
          </span>
          {hasActiveFilters && (
            <button
              type="button"
              onClick={onReset}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Bloom Level Pill Filter Buttons */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 pt-1 no-scrollbar">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 mr-1 flex items-center gap-1 flex-shrink-0">
          <Filter className="w-3.5 h-3.5" /> Bloom:
        </span>
        {bloomLevels.map((lvl) => {
          const isSelected = selectedBloom === lvl.value;
          return (
            <button
              key={lvl.value}
              type="button"
              onClick={() => onBloomChange(lvl.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                isSelected
                  ? 'bg-slate-900 dark:bg-sky-600 text-white shadow-xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {lvl.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};
