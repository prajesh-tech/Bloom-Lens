import { afterEach, expect, it, vi } from 'vitest';
import { analysisApi } from '../src/services/analysisApi';
import { historyApi } from '../src/services/historyApi';
import { MOCK_PAPERS, MOCK_QUESTIONS_MAP } from '../src/services/mockData';

vi.mock('../src/utils/latency', () => ({ simulateMockLatency: async () => {} }));
afterEach(() => { vi.unstubAllEnvs(); });

it('keeps exported fixtures and returned snapshots isolated from mutations', async () => {
  vi.stubEnv('VITE_USE_MOCK_API', 'true');
  const original = structuredClone({ papers: MOCK_PAPERS, questions: MOCK_QUESTIONS_MAP });
  await analysisApi.patchQuestion(MOCK_QUESTIONS_MAP[101][0].id, { question_text: 'A private mock correction.' });
  expect(MOCK_QUESTIONS_MAP).toEqual(original.questions);
  const paper = await analysisApi.uploadQuestionPaper({ subject_code: 'NEW', subject_name: 'New subject',
    examination_type: 'Internal', maximum_marks: 10, file: new File(['paper'], 'paper.pdf') });
  expect(MOCK_PAPERS).toEqual(original.papers);
  const history = await historyApi.getHistory();
  expect(history.items.some((item) => item.id === paper.id)).toBe(true);
  history.items[0].subject_name = 'Caller mutation';
  expect((await historyApi.getHistory()).items[0].subject_name).not.toBe('Caller mutation');
  await analysisApi.deleteQuestionPaper(paper.id);
  expect(MOCK_PAPERS).toEqual(original.papers);
});
