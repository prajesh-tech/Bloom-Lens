import React from 'react';
import { getBloomConfig } from '../../config/bloomConfig';

interface BloomBadgeProps {
  level?: string | null;
  showCode?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const BloomBadge: React.FC<BloomBadgeProps> = ({
  level,
  showCode = true,
  size = 'md',
  className = '',
}) => {
  if (!level) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200 rounded-md">
        Not Classified
      </span>
    );
  }

  const config = getBloomConfig(level);

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs font-semibold',
    lg: 'px-3 py-1.5 text-sm font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border font-medium transition-all ${config.badgeClass} ${sizeClasses[size]} ${className}`}
    >
      <span
        className="w-2 h-2 rounded-full flex-shrink-0"
        style={{ backgroundColor: config.chartColor }}
      />
      {showCode && <span className="font-mono text-[10px] uppercase opacity-75 font-bold">[{config.code}]</span>}
      <span>{config.label}</span>
    </span>
  );
};
