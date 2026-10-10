import React from 'react';
import { getBloomConfig } from '../../config/bloomConfig';

export const CustomTooltip: React.FC<any> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const levelName = data.name || data.bloom_level;
    const config = getBloomConfig(levelName);

    // Detect chart mode: bar chart sends `value` (percentage) + total_marks;
    // donut chart sends question_count + question_count_percentage.
    const isMarksMode = data.total_marks !== undefined && data.question_count_percentage === undefined;

    const primaryLabel = isMarksMode ? 'Total Marks' : 'Question Count';
    const primaryValue = isMarksMode
      ? `${data.total_marks ?? 0} marks`
      : `${data.question_count ?? data.value ?? 0} Questions`;

    const pct = isMarksMode
      ? (data.value ?? 0)  // value is already the marks_percentage for bar chart
      : (data.question_count_percentage ?? 0);

    return (
      <div className="bg-slate-900/95 dark:bg-slate-950/95 text-white rounded-xl p-3.5 shadow-2xl text-xs font-sans border border-slate-700/80 space-y-1 relative z-50">
        <div className="flex items-center gap-2 border-b border-slate-700/80 pb-1.5 mb-1.5">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: config.chartColor }}
          />
          <span className="font-bold text-sm text-slate-100">{config.label}</span>
          <span className="font-mono text-[10px] text-slate-400">[{config.code}]</span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-400">{primaryLabel}:</span>
          <span className="font-mono font-bold text-slate-100">{primaryValue}</span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-400">Distribution:</span>
          <span className="font-mono font-bold text-sky-400">{pct}%</span>
        </div>
      </div>
    );
  }
  return null;
};
