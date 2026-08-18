import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular';
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'rectangular',
  className,
  ...props
}) => {
  const baseStyles = 'animate-pulse bg-slate-200/80';

  const variantStyles = {
    text: 'h-4 w-full rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  return (
    <div
      className={twMerge(clsx(baseStyles, variantStyles[variant], className))}
      {...props}
    />
  );
};
