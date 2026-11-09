import { expect, it } from 'vitest';
import { paperBloomDistributions } from '../src/utils/paperDistribution';
import { QuestionAnalysis } from '../src/types/question';

it('counts nested leaves and excludes unknown Bloom levels from L1', () => {
  const base: QuestionAnalysis = { id: 1, question_paper_id: 1, question_number: 'Q1', original_text: 'Answer both.', marks: 10, review_status: 'AUTO_CLASSIFIED' };
  const result = paperBloomDistributions([{ ...base, sub_questions: [
    { ...base, id: 2, question_number: 'Q1(a)', marks: 5, effective_bloom_level: 'L2' },
    { ...base, id: 3, question_number: 'Q1(b)', marks: 5, effective_bloom_level: null },
  ] }]);
  expect(result.find((level) => level.bloom_level === 'L1')?.question_count).toBe(0);
  expect(result.find((level) => level.bloom_level === 'L2')?.question_count).toBe(1);
  expect(result.reduce((sum, level) => sum + level.total_marks, 0)).toBe(5);
});
