import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  hoverEffect = false,
  ...props
}) => {
  return (
    <div
      className={twMerge(
        clsx(
          'bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-xl p-5 shadow-xs transition-all text-slate-900 dark:text-slate-100',
          hoverEffect && 'hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-sm',
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
};
