import { BloomLevel } from './bloom';

export interface OverviewAnalytics {
  uncertain_paper_ids?: number[];
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
  uncertain_paper_ids?: number[];
  distributions: BloomDistributionItem[];
  total_questions: number;
  total_marks: number;
}

export interface TopicFrequencyItem {
  topic_id?: number;
  topic: string;
  frequency: number;
  total_marks: number;
  bloom_breakdown?: Record<string, number>;
}

export interface HistoricalTrendItem {
  unknown_question_count?: number;
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
  uncertain_paper_ids?: number[];
  metric_type: 'count' | 'marks_weighted';
  trends: HistoricalTrendItem[];
}

export interface Subject {
  id: number;
  code: string;
  name: string;
}

export interface TopicAnalyticsData {
  topics: TopicFrequencyItem[];
  uncertain_paper_ids?: number[];
}

export interface QuestionAnalyticsData {
  repeated_questions_count: number;
  similar_questions_count: number;
  highest_mark_questions: { id: number; question_number: string; text: string; marks: number; unit?: string | null }[];
  question_type_distribution: Record<string, number>;
}
