import { useSubjectsQuery } from '../../services/queries';
import { Button } from './Button';

export function SubjectFilter({ value, onChange }: { value?: number; onChange: (value?: number) => void }) {
  const subjects = useSubjectsQuery();
  return <div className="space-y-2">
    <label className="font-semibold text-sm">Subject
      <select className="ml-3 rounded border p-2 bg-white dark:bg-slate-900" aria-label="Subject" value={value ?? ''} onChange={(event) => onChange(event.target.value ? Number(event.target.value) : undefined)}>
        <option value="">All subjects</option>
        {subjects.data?.map((subject) => <option key={subject.id} value={subject.id}>{subject.code} — {subject.name}</option>)}
      </select>
    </label>
    {subjects.isError && <p role="alert">Unable to load subjects. <Button onClick={() => subjects.refetch()}>Retry</Button></p>}
  </div>;
}
