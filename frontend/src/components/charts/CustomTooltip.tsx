import React from 'react';
import { getBloomConfig } from '../../config/bloomConfig';

export const CustomTooltip: React.FC<any> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const levelName = data.name || data.bloom_level;
    const config = getBloomConfig(levelName);

    const count = data.question_count !== undefined ? data.question_count : data.value;
    const pct = data.question_count_percentage !== undefined
      ? data.question_count_percentage
      : data.marks_percentage !== undefined
      ? data.marks_percentage
      : 0;

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
          <span className="text-slate-400">Question Count:</span>
          <span className="font-mono font-bold text-slate-100">{count} Questions</span>
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
