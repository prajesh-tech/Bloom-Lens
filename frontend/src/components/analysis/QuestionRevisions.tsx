import { useQuestionRevisionsQuery } from '../../services/queries';
import { Button } from '../common/Button';

export function QuestionRevisions({ questionId }: { questionId: number }) {
  const history = useQuestionRevisionsQuery(questionId);
  return <section className="space-y-3 pt-4">
    <h3 className="font-semibold">Review history</h3>
    {history.isPending && <p role="status">Loading review history…</p>}
    {history.isError && <p role="alert">Unable to load review history. <Button onClick={() => history.refetch()}>Retry</Button></p>}
    {history.data?.length === 0 && <p>No review changes recorded.</p>}
    {history.data?.map((revision) => <article key={revision.id} className="border rounded-lg p-3 space-y-2">
      <p className="text-sm">{revision.acting_user} · <time dateTime={revision.created_at}>{new Date(revision.created_at).toLocaleString()}</time></p>
      <dl className="text-xs space-y-1">{Object.keys(revision.new_value).filter((key) => JSON.stringify(revision.old_value[key]) !== JSON.stringify(revision.new_value[key])).map((key) =>
        <div key={key}><dt className="font-semibold">{key.replace(/_/g, ' ')}</dt><dd className="break-words">{JSON.stringify(revision.old_value[key]) ?? 'unset'} → {JSON.stringify(revision.new_value[key]) ?? 'unset'}</dd></div>
      )}</dl>
    </article>)}
  </section>;
}
