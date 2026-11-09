import { MOCK_PAPERS, MOCK_QUESTIONS_MAP } from './mockData';
import { QuestionPaper } from '../types/paper';
import { QuestionAnalysis, QuestionRevision } from '../types/question';

interface MockState {
  papers: QuestionPaper[];
  questions: Record<number, QuestionAnalysis[]>;
  revisions: Record<number, QuestionRevision[]>;
}

let state: MockState = structuredClone({ papers: MOCK_PAPERS, questions: MOCK_QUESTIONS_MAP, revisions: {} });
export const readMockState = (): MockState => structuredClone(state);
export const writeMockState = (next: MockState): void => { state = structuredClone(next); };
