import { useSimilarQuestionsQuery } from '../../services/queries';
import { Button } from '../common/Button';

export function SimilarQuestions({ questionId }: { questionId: number }) {
  const similar = useSimilarQuestionsQuery(questionId);
  return <section className="space-y-3 pt-4">
    <h3 className="font-semibold">Similar and repeated questions</h3>
    {similar.isPending && <p role="status">Loading similar questions…</p>}
    {similar.isError && <div role="alert">Unable to load similar questions. <Button onClick={() => similar.refetch()}>Retry</Button></div>}
    {similar.data?.length === 0 && <p>No similar questions found.</p>}
    {similar.data?.map((question) => <article className="border rounded-lg p-3" key={question.id}>
      <p>{question.target_question_text}</p>
      <p className="text-xs mt-1">{question.target_question_number} · {question.classification.replace(/_/g, ' ')} · {(question.similarity_score * 100).toFixed(1)}% similarity</p>
    </article>)}
  </section>;
}
