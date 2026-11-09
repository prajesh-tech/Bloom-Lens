import { BLOOM_CONFIG, getBloomCode } from '../config/bloomConfig';
import { QuestionAnalysis } from '../types/question';
import { BloomDistributionItem } from '../types/analytics';

export function paperBloomDistributions(questions: QuestionAnalysis[]): BloomDistributionItem[] {
  const all = new Map<number, QuestionAnalysis>();
  const parents = new Set<number>();
  const visit = (question: QuestionAnalysis) => {
    all.set(question.id, question);
    if (question.parent_question_id != null) parents.add(question.parent_question_id);
    if (question.sub_questions?.length) parents.add(question.id);
    question.sub_questions?.forEach(visit);
  };
  questions.forEach(visit);
  const leaves = [...all.values()].filter((question) => !parents.has(question.id));
  const known = leaves.filter((question) => getBloomCode(question.effective_bloom_level || question.ai_bloom_level || ''));
  const totalMarks = known.reduce((sum, question) => sum + (question.marks ?? 0), 0);
  return Object.values(BLOOM_CONFIG).map((level) => {
    const matching = known.filter((question) => getBloomCode(question.effective_bloom_level || question.ai_bloom_level || '') === level.code);
    const marks = matching.reduce((sum, question) => sum + (question.marks ?? 0), 0);
    return { bloom_level: level.code, name: level.label, question_count: matching.length,
      question_count_percentage: known.length ? Number((matching.length / known.length * 100).toFixed(2)) : 0,
      total_marks: marks, marks_percentage: totalMarks ? Number((marks / totalMarks * 100).toFixed(2)) : 0 };
  });
}
