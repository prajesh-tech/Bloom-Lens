import { useState } from 'react';
import { SubjectFilter } from '../components/common/SubjectFilter';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { BloomBarChart } from '../components/charts/BloomBarChart';
import { useBloomAnalyticsQuery, useTopicAnalyticsQuery, useQuestionAnalyticsQuery, useTrendsQuery } from '../services/queries';

export function Analytics() {
  const [subjectId, setSubjectId] = useState<number>();
  const [metric, setMetric] = useState<'count' | 'marks_weighted'>('marks_weighted');
  const bloom = useBloomAnalyticsQuery(subjectId);
  const topics = useTopicAnalyticsQuery(subjectId);
  const questions = useQuestionAnalyticsQuery(subjectId);
  const trends = useTrendsQuery(metric, subjectId);
  const queries = [bloom, topics, questions, trends];
  return <div className="space-y-6">
    <h1 className="text-2xl font-bold">Analytics</h1>
    <SubjectFilter value={subjectId} onChange={setSubjectId} />
    {queries.some((query) => query.isPending) && <p role="status">Loading analytics…</p>}
    {queries.some((query) => query.isError) && <p role="alert">Unable to load some analytics. <Button onClick={() => queries.forEach((query) => { void query.refetch(); })}>Retry</Button></p>}
    {!!(topics.data?.uncertain_paper_ids?.length || bloom.data?.uncertain_paper_ids?.length || trends.data?.uncertain_paper_ids?.length) && <p role="status">Optional question choices make these distributions uncertain; counts describe available questions.</p>}
    <div className="grid sm:grid-cols-2 gap-4">
      <Card><h2>Repeated questions</h2><p className="text-2xl font-bold">{questions.data?.repeated_questions_count ?? '—'}</p></Card>
      <Card><h2>Semantically similar questions</h2><p className="text-2xl font-bold">{questions.data?.similar_questions_count ?? '—'}</p></Card>
    </div>
    <Card className="space-y-4"><h2 className="font-semibold">Bloom distribution</h2>
      <label>Distribution metric <select aria-label="Distribution metric" value={metric} onChange={(event) => setMetric(event.target.value === 'count' ? 'count' : 'marks_weighted')} className="border rounded p-2 ml-2 bg-white dark:bg-slate-900">
        <option value="marks_weighted">Marks weighted</option><option value="count">Question count</option>
      </select></label>
      {bloom.data && <BloomBarChart data={bloom.data.distributions} metricType={metric} />}
    </Card>
    <Card className="space-y-3 overflow-x-auto"><h2 className="font-semibold">Topic analytics</h2>
      {topics.data?.topics.length === 0 && <p>No topic data available.</p>}
      <table className="w-full text-sm text-left"><thead><tr><th>Topic</th><th>Questions</th><th>Marks</th><th>Bloom breakdown</th></tr></thead>
        <tbody>{topics.data?.topics.map((topic, index) => <tr key={topic.topic_id ?? `${topic.topic}-${index}`} className="border-t">
          <td className="py-3">{topic.topic}</td><td>{topic.frequency}</td><td>{topic.total_marks}</td>
          <td>{Object.entries(topic.bloom_breakdown ?? {}).map(([level, count]) => `${level}: ${count}`).join(', ') || 'Unclassified'}</td>
        </tr>)}</tbody></table>
    </Card>
    <Card className="space-y-3 overflow-x-auto"><h2 className="font-semibold">Exam-year trends</h2>
      {trends.data?.trends.length === 0 && <p>No historical trend data available.</p>}
      <table className="w-full text-sm text-left"><thead><tr><th>Paper</th><th>Exam date</th><th>Unknown Bloom questions</th>{['L1', 'L2', 'L3', 'L4', 'L5', 'L6'].map((level) => <th key={level}>{level}</th>)}</tr></thead>
        <tbody>{trends.data?.trends.map((trend, index) => <tr className="border-t" key={trend.paper_id ?? `${trend.paper}-${index}`}>
          <td className="py-3">{trend.paper}</td><td>{trend.year ?? 'Unknown'}</td><td>{trend.unknown_question_count ?? 0}</td>{([trend.L1, trend.L2, trend.L3, trend.L4, trend.L5, trend.L6]).map((value, level) => <td key={level}>{value.toFixed(1)}%</td>)}
        </tr>)}</tbody></table>
    </Card>
  </div>;
}
