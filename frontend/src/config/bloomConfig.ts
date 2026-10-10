import { BloomConfigMap, BloomLevel, BloomCode, BloomConfigItem } from '../types/bloom';

export const BLOOM_CONFIG: BloomConfigMap = {
  Remember: {
    code: 'L1',
    label: 'Remember',
    description: 'Recall facts and basic concepts',
    badgeClass: 'bg-sky-50 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 border-sky-200 dark:border-sky-800',
    borderClass: 'border-sky-200 dark:border-sky-800/80',
    bgClass: 'bg-sky-50 dark:bg-sky-950/40',
    textClass: 'text-sky-700 dark:text-sky-400',
    chartColor: '#0284c7',
    verbs: ['Define', 'List', 'Identify', 'State', 'Name', 'Recall'],
  },
  Understand: {
    code: 'L2',
    label: 'Understand',
    description: 'Explain ideas or concepts',
    badgeClass: 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800',
    borderClass: 'border-blue-200 dark:border-blue-800/80',
    bgClass: 'bg-blue-50 dark:bg-blue-950/40',
    textClass: 'text-blue-700 dark:text-blue-400',
    chartColor: '#2563eb',
    verbs: ['Explain', 'Describe', 'Summarize', 'Discuss', 'Interpret'],
  },
  Apply: {
    code: 'L3',
    label: 'Apply',
    description: 'Use information in new situations',
    badgeClass: 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
    borderClass: 'border-emerald-200 dark:border-emerald-800/80',
    bgClass: 'bg-emerald-50 dark:bg-emerald-950/40',
    textClass: 'text-emerald-700 dark:text-emerald-400',
    chartColor: '#059669',
    verbs: ['Apply', 'Demonstrate', 'Calculate', 'Solve', 'Execute'],
  },
  Analyze: {
    code: 'L4',
    label: 'Analyze',
    description: 'Draw connections among ideas',
    badgeClass: 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800',
    borderClass: 'border-amber-200 dark:border-amber-800/80',
    bgClass: 'bg-amber-50 dark:bg-amber-950/40',
    textClass: 'text-amber-700 dark:text-amber-400',
    chartColor: '#d97706',
    verbs: ['Analyze', 'Compare', 'Differentiate', 'Contrast', 'Examine'],
  },
  Evaluate: {
    code: 'L5',
    label: 'Evaluate',
    description: 'Justify a stand or decision',
    badgeClass: 'bg-orange-50 dark:bg-orange-950/60 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-800',
    borderClass: 'border-orange-200 dark:border-orange-800/80',
    bgClass: 'bg-orange-50 dark:bg-orange-950/40',
    textClass: 'text-orange-700 dark:text-orange-400',
    chartColor: '#ea580c',
    verbs: ['Evaluate', 'Justify', 'Critique', 'Assess', 'Defend'],
  },
  Create: {
    code: 'L6',
    label: 'Create',
    description: 'Produce new or original work',
    badgeClass: 'bg-violet-50 dark:bg-violet-950/60 text-violet-700 dark:text-violet-300 border-violet-200 dark:border-violet-800',
    borderClass: 'border-violet-200 dark:border-violet-800/80',
    bgClass: 'bg-violet-50 dark:bg-violet-950/40',
    textClass: 'text-violet-700 dark:text-violet-400',
    chartColor: '#7c3aed',
    verbs: ['Design', 'Develop', 'Construct', 'Formulate', 'Architect'],
  },
};

export const BLOOM_CODE_TO_LABEL: Record<BloomCode, BloomLevel> = {
  L1: 'Remember',
  L2: 'Understand',
  L3: 'Apply',
  L4: 'Analyze',
  L5: 'Evaluate',
  L6: 'Create',
};

export const BLOOM_LABEL_TO_CODE: Record<BloomLevel, BloomCode> = {
  Remember: 'L1',
  Understand: 'L2',
  Apply: 'L3',
  Analyze: 'L4',
  Evaluate: 'L5',
  Create: 'L6',
};

function isBloomCode(level: string): level is BloomCode {
  return Object.prototype.hasOwnProperty.call(BLOOM_CODE_TO_LABEL, level);
}

export function getBloomCode(level?: string): BloomCode | undefined {
  if (!level) return undefined;

  const normalized = level.trim().toUpperCase();
  if (isBloomCode(normalized)) return normalized;

  const label = (Object.keys(BLOOM_LABEL_TO_CODE) as BloomLevel[]).find(
    (candidate) => candidate.toUpperCase() === normalized
  );
  return label ? BLOOM_LABEL_TO_CODE[label] : undefined;
}

export function getBloomConfig(level?: string): BloomConfigItem {
  if (!level) return BLOOM_CONFIG.Remember;
  
  // Handle code ("L1") or label ("Remember")
  if (level.toUpperCase() in BLOOM_CODE_TO_LABEL) {
    const label = BLOOM_CODE_TO_LABEL[level.toUpperCase() as BloomCode];
    return BLOOM_CONFIG[label];
  }

  const normalized = level.charAt(0).toUpperCase() + level.slice(1).toLowerCase();
  if (normalized in BLOOM_CONFIG) {
    return BLOOM_CONFIG[normalized as BloomLevel];
  }

  return BLOOM_CONFIG.Remember;
}
