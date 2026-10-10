import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Skeleton } from '../components/common/Skeleton';
import { BloomDonutChart } from '../components/charts/BloomDonutChart';
import { BloomBarChart } from '../components/charts/BloomBarChart';
import { HistoryTable } from '../components/history/HistoryTable';
import { useDashboardQueries } from '../services/queries';
import { UploadCloud, BrainCircuit, FileCheck2, Award, ArrowRight, Layers, BookOpen } from 'lucide-react';

export const Home: React.FC = () => {
  const navigate = useNavigate();
  const { overview, bloom, history } = useDashboardQueries();
  const loading = overview.isLoading || bloom.isLoading || history.isLoading;
  const overviewData = overview.data;
  const bloomAnalytics = bloom.data;
  const recentPapers = history.data?.items || [];

  return (
    <div className="space-y-8 animate-in fade-in">
      {/* Hero Welcome Banner */}
      <div className="bg-slate-900 text-white rounded-3xl p-8 sm:p-10 shadow-xl relative overflow-hidden">
        <div className="absolute -right-10 -bottom-10 opacity-10 pointer-events-none">
          <BrainCircuit className="w-96 h-96 text-sky-400" />
        </div>
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-mono text-sky-400">
            <Layers className="w-3.5 h-3.5" /> Bloom's Taxonomy Cognitive Engine
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            AI-Powered Question Paper Cognitive Level Analysis
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Extract historical question papers, classify questions across Revised Bloom’s Taxonomy levels (L1–L6), evaluate cognitive distributions, and inspect repeated questions.
          </p>
          <div className="pt-2">
            <Button
              variant="primary"
              size="lg"
              className="bg-white text-slate-900 hover:bg-slate-100 font-semibold"
              onClick={() => navigate('/analyze')}
              leftIcon={<UploadCloud className="w-5 h-5 text-slate-900" />}
            >
              Analyze Question Paper
            </Button>
          </div>
        </div>
      </div>

      {/* Macro Overview Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Papers Analyzed</span>
            <div className="w-8 h-8 rounded-lg bg-sky-50 dark:bg-sky-950/60 border border-sky-200/60 dark:border-sky-800/80 flex items-center justify-center">
              <FileCheck2 className="w-4 h-4 text-sky-600 dark:text-sky-400" />
            </div>
          </div>
          {loading ? (
            <Skeleton className="h-8 w-24" />
          ) : (
            <div className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">
              {overviewData?.papers_analyzed || 0}
            </div>
          )}
        </Card>

        <Card className="space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Questions Extracted</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200/60 dark:border-indigo-800/80 flex items-center justify-center">
              <BrainCircuit className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            </div>
          </div>
          {loading ? (
            <Skeleton className="h-8 w-24" />
          ) : (
            <div className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">
              {overviewData?.questions_analyzed || 0}
            </div>
          )}
        </Card>

        <Card className="space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Subjects Cataloged</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200/60 dark:border-emerald-800/80 flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
          </div>
          {loading ? (
            <Skeleton className="h-8 w-24" />
          ) : (
            <div className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">
              {overviewData?.subjects_count || 0}
            </div>
          )}
        </Card>

        <Card className="space-y-2">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Marks Analyzed</span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 dark:bg-purple-950/60 border border-purple-200/60 dark:border-purple-800/80 flex items-center justify-center">
              <Award className="w-4 h-4 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          {loading ? (
            <Skeleton className="h-8 w-24" />
          ) : (
            <div className="text-3xl font-extrabold font-mono text-slate-900 dark:text-white">
              {overviewData?.total_relevant_marks || 0}
            </div>
          )}
        </Card>
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Donut Chart */}
        <Card className="space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Overall Bloom Taxonomy Distribution</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">Cognitive level breakdown across all analyzed questions</p>
          </div>
          {loading || !bloomAnalytics ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <BloomDonutChart data={bloomAnalytics.distributions} />
          )}
        </Card>

        {/* Bar Chart */}
        <Card className="space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Marks-Weighted Cognitive Breakdown</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">Percentage of total exam marks assigned to each Bloom level</p>
          </div>
          {loading || !bloomAnalytics ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <BloomBarChart data={bloomAnalytics.distributions} metricType="marks_weighted" />
          )}
        </Card>
      </div>

      {/* Recent Analysis History Preview */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Recent Question Paper Analyses</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">Select a paper to inspect detailed questions and Bloom levels</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/history')}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            View All History
          </Button>
        </div>

        {loading ? <Skeleton className="h-48 w-full" /> : <HistoryTable papers={recentPapers} />}
      </div>
    </div>
  );
};
