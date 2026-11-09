export interface QuestionAnalysis {
  id: number;
  question_paper_id: number;
  parent_question_id?: number | null;
  question_number: string;
  original_text: string;
  normalized_text?: string;
  co_mapping?: Record<string, string[]> | null;
  choice_group?: string | null;
  marks?: number | null;
  marks_confidence?: 'high' | 'medium' | 'low' | null;

  ai_bloom_level?: string | null;
  human_bloom_level?: string | null;
  effective_bloom_level?: string | null;
  bloom_confidence?: number | null;
  bloom_explanation?: string | null;

  ai_question_type?: string | null;
  human_question_type?: string | null;
  question_type?: string | null;

  unit?: string | null;
  topic?: string | null;
  extraction_confidence?: number | null;
  review_status: 'AUTO_CLASSIFIED' | 'REVIEWED' | 'CORRECTED' | 'FLAGGED';

  ai_analysis_metadata?: {
    classifier_source?: 'hybrid' | 'gemini_verified';
    gemini_verification_status?: string;
    detected_verbs?: string[];
    cognitive_operation?: string;
    component_scores?: Record<string, number>;
    candidate_scores?: Record<string, number>;
    needs_reanalysis?: boolean;
    confidence_kind?: string;
    embedding_backend?: { backend: string; model: string; version: string };
  } | null;

  sub_questions?: QuestionAnalysis[];
}

export interface QuestionPatchPayload {
  question_text?: string;
  marks?: number;
  topic_name?: string;
  unit?: string;
  bloom_level?: string;
  question_type?: string;
  co_mapping?: Record<string, string[]> | null;
  choice_group?: string | null;
}

export interface SimilarQuestion {
  id: number;
  source_question_id: number;
  target_question_id: number;
  target_question_text?: string | null;
  target_question_number?: string | null;
  similarity_score: number;
  similarity_type: string;
  classification: string;
}

export interface QuestionRevision {
  id: number;
  question_id: number | null;
  acting_user: string;
  created_at: string;
  old_value: Record<string, unknown>;
  new_value: Record<string, unknown>;
}

export interface QuestionFilterState {
  searchQuery: string;
  selectedBloomLevel: string; // 'ALL' | 'Remember' | ...
  selectedUnit: string;
  selectedQuestionType: string;
}
