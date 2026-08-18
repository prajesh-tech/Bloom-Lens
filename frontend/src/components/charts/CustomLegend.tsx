import React from 'react';
import { getBloomConfig } from '../../config/bloomConfig';
import { BloomDistributionItem } from '../../types/analytics';

interface CustomLegendProps {
  data: BloomDistributionItem[];
  onHoverItem?: (level: string | null) => void;
}

export const CustomLegend: React.FC<CustomLegendProps> = ({ data, onHoverItem }) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 pt-4 border-t border-slate-100 dark:border-slate-800">
      {data.map((item) => {
        const config = getBloomConfig(item.name || item.bloom_level);

        return (
          <div
            key={item.bloom_level}
            onMouseEnter={() => onHoverItem && onHoverItem(item.name)}
            onMouseLeave={() => onHoverItem && onHoverItem(null)}
            className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors border border-slate-200/60 dark:border-slate-700/60"
          >
            <div className="flex items-center gap-2 overflow-hidden">
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: config.chartColor }}
              />
              <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                {config.label}
              </span>
            </div>
            <div className="flex items-center gap-2 font-mono text-xs text-slate-600 dark:text-slate-400 flex-shrink-0 pl-2">
              <span className="font-bold text-slate-900 dark:text-white">{item.question_count}</span>
              <span className="text-[10px] text-slate-400 dark:text-slate-500">({item.question_count_percentage}%)</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
