import { BloomLevel } from './bloom';

export interface OverviewAnalytics {
  papers_analyzed: number;
  questions_analyzed: number;
  subjects_count: number;
  topics_count: number;
  total_relevant_marks: number;
}

export interface BloomDistributionItem {
  bloom_level: string; // L1 - L6
  name: BloomLevel;
  question_count: number;
  question_count_percentage: number;
  total_marks: number;
  marks_percentage: number;
}

export interface BloomAnalyticsData {
  distributions: BloomDistributionItem[];
  total_questions: number;
  total_marks: number;
}

export interface TopicFrequencyItem {
  topic: string;
  frequency: number;
  total_marks: number;
  bloom_breakdown?: Record<string, number>;
}

export interface HistoricalTrendItem {
  paper_id?: number;
  paper: string;
  year?: string;
  examination_type?: string;
  subject_code?: string;
  L1: number;
  L2: number;
  L3: number;
  L4: number;
  L5: number;
  L6: number;
}

export interface TrendsAnalyticsData {
  metric_type: 'count' | 'marks_weighted';
  trends: HistoricalTrendItem[];
}
