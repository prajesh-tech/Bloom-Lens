import React from 'react';
import { HistoryTable } from '../components/history/HistoryTable';
import { Skeleton } from '../components/common/Skeleton';
import { History as HistoryIcon } from 'lucide-react';
import { toast } from '../components/common/Toast';
import { useDeletePaperMutation, useHistoryQuery } from '../services/queries';

export const History: React.FC = () => {
  const history = useHistoryQuery(1, 50);
  const deletePaper = useDeletePaperMutation();
  const papers = history.data?.items || [];

  const handleDeletePaper = async (paperId: number) => {
    try {
      await deletePaper.mutateAsync(paperId);
      toast.success('Paper deleted successfully from frontend and backend.');
    } catch (err: any) {
      toast.error('Failed to delete paper: ' + (err.message || 'Unknown error'));
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center shadow-xs">
          <HistoryIcon className="w-5 h-5 text-sky-400" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Analysis History
          </h1>
          <p className="text-xs text-slate-500 font-mono">
            View and inspect previously uploaded examination question paper analyses
          </p>
        </div>
      </div>

      {history.isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <HistoryTable papers={papers} onDeletePaper={handleDeletePaper} />
      )}
    </div>
  );
};
