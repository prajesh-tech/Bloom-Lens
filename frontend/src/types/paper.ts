export interface QuestionPaper {
  id: number;
  subject_id?: number;
  subject_code: string;
  subject_name: string;
  examination_type: string;
  maximum_marks: number;
  original_filename: string;
  stored_file_path?: string;
  upload_timestamp: string;
  year_date?: string;
  processing_status: 'UPLOADED' | 'PROCESSING' | 'EXTRACTED' | 'ANALYZING' | 'COMPLETED' | 'REVIEW_REQUIRED' | 'FAILED';
  extraction_status: 'PENDING' | 'SUCCESS' | 'PARTIAL' | 'FAILED';
  validation_status: 'NOT_VALIDATED' | 'VALID' | 'MISMATCH' | 'UNCERTAIN' | 'REQUIRES_REVIEW';
  optional_question_flag: boolean;
  validation_metadata?: {
    status?: string;
    maximum_marks?: number;
    extracted_marks?: number;
    missing_marks_count?: number;
    possible_reasons?: string[];
  };
  total_questions?: number;
}

export interface PaperUploadPayload {
  subject_code: string;
  subject_name: string;
  examination_type: string;
  maximum_marks: number;
  year_date?: string;
  file: File;
}

export interface PerformanceEstimate {
  estimated_pass_percentage: number | null;
  estimated_average_marks: number | null;
  reason?: string | null;
}
