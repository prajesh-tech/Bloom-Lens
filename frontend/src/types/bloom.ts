export type BloomLevel =
  | 'Remember'
  | 'Understand'
  | 'Apply'
  | 'Analyze'
  | 'Evaluate'
  | 'Create';

export type BloomCode = 'L1' | 'L2' | 'L3' | 'L4' | 'L5' | 'L6';

export interface BloomConfigItem {
  code: BloomCode;
  label: BloomLevel;
  description: string;
  badgeClass: string;
  borderClass: string;
  bgClass: string;
  textClass: string;
  chartColor: string;
  verbs: string[];
}

export type BloomConfigMap = Record<BloomLevel, BloomConfigItem>;
