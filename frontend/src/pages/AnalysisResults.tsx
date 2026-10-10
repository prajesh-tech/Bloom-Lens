import React, { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { AnalysisHeader } from '../components/analysis/AnalysisHeader';
import { SummaryCards } from '../components/analysis/SummaryCards';
import { PerformanceEstimateCard } from '../components/analysis/PerformanceEstimateCard';
import { QuestionFilterBar } from '../components/analysis/QuestionFilterBar';
import { QuestionTable } from '../components/analysis/QuestionTable';
import { QuestionDrawer } from '../components/analysis/QuestionDrawer';
import { BloomDonutChart } from '../components/charts/BloomDonutChart';
import { BloomBarChart } from '../components/charts/BloomBarChart';
import { Card } from '../components/common/Card';
import { Skeleton } from '../components/common/Skeleton';
import { useAnalysisResultQueries, usePatchQuestionMutation } from '../services/queries';
import { BloomLevel } from '../types/bloom';
import { QuestionAnalysis, QuestionPatchPayload } from '../types/question';
import { BloomDistributionItem } from '../types/analytics';
import { getBloomCode } from '../config/bloomConfig';

const EMPTY_QUESTIONS: QuestionAnalysis[] = [];

export const AnalysisResults: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const paperId = parseInt(id || '101', 10);

  const { paper: paperQuery, questions: questionsQuery } = useAnalysisResultQueries(paperId);
  const patchQuestion = usePatchQuestionMutation(paperId);
  const paper = paperQuery.data || null;
  const questions = questionsQuery.data || EMPTY_QUESTIONS;
  const loading = paperQuery.isLoading || questionsQuery.isLoading;

  // Filter & Drawer State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBloom, setSelectedBloom] = useState('ALL');
  const [selectedQuestion, setSelectedQuestion] = useState<QuestionAnalysis | null>(null);

  // Combined Search + Bloom Filter Logic
  const filteredQuestions = useMemo(() => {
    const targetBloomCode = getBloomCode(selectedBloom);

    return questions.filter((q) => {
      // 1. Text or Question ID Search (case-insensitive)
      const qText = q.original_text.toLowerCase();
      const qNum = q.question_number.toLowerCase();
      const query = searchQuery.toLowerCase();
      const matchesSearch = !query || qText.includes(query) || qNum.includes(query);

      // 2. Bloom Level Filter
      const effLevel = (q.effective_bloom_level || q.ai_bloom_level || '').toUpperCase();
      const effBloomCode = getBloomCode(effLevel);
      const matchesBloom =
        selectedBloom === 'ALL' ||
        (effBloomCode !== undefined && effBloomCode === targetBloomCode);

      return matchesSearch && matchesBloom;
    });
  }, [questions, searchQuery, selectedBloom]);

  // Paper-specific Bloom Distributions computed from leaf questions only.
  // Leaf questions are those with no sub_questions (i.e. not parent containers).
  // This prevents double-counting marks when parents and their children are both
  // present in the flat questions list returned by the API.
  const paperBloomDistributions = useMemo<BloomDistributionItem[]>(() => {
    const levels: { code: string; name: BloomLevel }[] = [
      { code: 'L1', name: 'Remember' },
      { code: 'L2', name: 'Understand' },
      { code: 'L3', name: 'Apply' },
      { code: 'L4', name: 'Analyze' },
      { code: 'L5', name: 'Evaluate' },
      { code: 'L6', name: 'Create' },
    ];

    // Collect IDs that are referenced as parent by any other question
    const parentIds = new Set<number>();
    questions.forEach((q) => {
      if (q.parent_question_id != null) parentIds.add(q.parent_question_id);
    });

    // Leaf = not a parent AND has no populated sub_questions array
    const leafQuestions = questions.filter(
      (q) =>
        !parentIds.has(q.id) &&
        (!q.sub_questions || q.sub_questions.length === 0)
    );

    const totalQ = leafQuestions.length;
    const totalM = leafQuestions.reduce((sum, q) => sum + (q.marks || 0), 0);

    const counts: Record<string, number> = { L1: 0, L2: 0, L3: 0, L4: 0, L5: 0, L6: 0 };
    const marksSum: Record<string, number> = { L1: 0, L2: 0, L3: 0, L4: 0, L5: 0, L6: 0 };

    leafQuestions.forEach((q) => {
      const lvlStr = (q.effective_bloom_level || q.ai_bloom_level || '').toUpperCase();
      let code = 'L1';
      if (lvlStr.includes('UNDERSTAND') || lvlStr === 'L2') code = 'L2';
      else if (lvlStr.includes('APPLY') || lvlStr === 'L3') code = 'L3';
      else if (lvlStr.includes('ANALYZE') || lvlStr === 'L4') code = 'L4';
      else if (lvlStr.includes('EVALUATE') || lvlStr === 'L5') code = 'L5';
      else if (lvlStr.includes('CREATE') || lvlStr === 'L6') code = 'L6';
      else code = 'L1';

      counts[code] = (counts[code] || 0) + 1;
      marksSum[code] = (marksSum[code] || 0) + (q.marks || 0);
    });

    return levels.map((lvl) => {
      const qCnt = counts[lvl.code] || 0;
      const mSum = marksSum[lvl.code] || 0;
      return {
        bloom_level: lvl.code,
        name: lvl.name,
        question_count: qCnt,
        question_count_percentage: totalQ > 0 ? Number(((qCnt / totalQ) * 100).toFixed(2)) : 0,
        total_marks: mSum,
        marks_percentage: totalM > 0 ? Number(((mSum / totalM) * 100).toFixed(2)) : 0,
      };
    });
  }, [questions]);

  const handleSaveOverride = async (questionId: number, payload: QuestionPatchPayload) => {
    const updated = await patchQuestion.mutateAsync({ questionId, payload });

    if (selectedQuestion && selectedQuestion.id === questionId) {
      setSelectedQuestion((prev) => (prev ? { ...prev, ...updated } : null));
    }
  };

  if (loading || !paper) {
    return (
      <div className="space-y-6 animate-in fade-in">
        <Skeleton className="h-28 w-full" />
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in">
      {/* Header */}
      <AnalysisHeader paper={paper} questions={questions} />

      {/* Summary Stat Cards */}
      <SummaryCards paper={paper} questionCount={questions.length} />

      {/* Estimated Student Performance Card */}
      <PerformanceEstimateCard paperId={paper.id} maxMarks={paper.maximum_marks} />

      {/* Visual Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Bloom Level Question Distribution</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">Cognitive level breakdown across paper questions</p>
          </div>
          <BloomDonutChart data={paperBloomDistributions} />
        </Card>

        <Card className="space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Marks-Weighted Cognitive Weight</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">Percentage of total marks assigned to cognitive levels</p>
          </div>
          <BloomBarChart data={paperBloomDistributions} metricType="marks_weighted" />
        </Card>
      </div>

      {/* Question Table & Filter Bar */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">Analyzed Question Breakdown</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
            Click any question row to open the inspect drawer and perform human overrides
          </p>
        </div>

        <QuestionFilterBar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selectedBloom={selectedBloom}
          onBloomChange={setSelectedBloom}
          onReset={() => {
            setSearchQuery('');
            setSelectedBloom('ALL');
          }}
          filteredCount={filteredQuestions.length}
          totalCount={questions.length}
        />

        <QuestionTable
          questions={filteredQuestions}
          selectedQuestionId={selectedQuestion?.id || null}
          onSelectQuestion={(q) => setSelectedQuestion(q)}
        />
      </div>

      {/* Right-Side Slide-Over Question Details Drawer */}
      <QuestionDrawer
        question={selectedQuestion}
        isOpen={selectedQuestion !== null}
        onClose={() => setSelectedQuestion(null)}
        onSaveOverride={handleSaveOverride}
      />
    </div>
  );
};
