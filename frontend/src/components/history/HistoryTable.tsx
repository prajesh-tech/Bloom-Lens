import React, { useState } from 'react';
import { QuestionPaper } from '../../types/paper';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { formatDate } from '../../utils/formatters';
import { useNavigate } from 'react-router-dom';
import { Search, FileText, ArrowRight, Trash2, AlertTriangle } from 'lucide-react';

interface HistoryTableProps {
  papers: QuestionPaper[];
  onDeletePaper?: (paperId: number) => void;
}

export const HistoryTable: React.FC<HistoryTableProps> = ({ papers, onDeletePaper }) => {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [deletingPaperId, setDeletingPaperId] = useState<number | null>(null);

  const filtered = papers.filter(
    (p) =>
      p.subject_name.toLowerCase().includes(search.toLowerCase()) ||
      p.subject_code.toLowerCase().includes(search.toLowerCase()) ||
      p.original_filename.toLowerCase().includes(search.toLowerCase())
  );

  const confirmDelete = () => {
    if (deletingPaperId && onDeletePaper) {
      onDeletePaper(deletingPaperId);
      setDeletingPaperId(null);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl shadow-xs overflow-hidden space-y-4 p-4 sm:p-6 transition-colors">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search analysis history..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </div>
        <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
          Total Analyzed Papers: <strong className="text-slate-900 dark:text-white">{filtered.length}</strong>
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              <th className="py-3.5 px-4">Subject</th>
              <th className="py-3.5 px-4">Filename</th>
              <th className="py-3.5 px-4">Exam Type</th>
              <th className="py-3.5 px-4">Upload Date</th>
              <th className="py-3.5 px-4">Status</th>
              <th className="py-3.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200/80 dark:divide-slate-800 text-sm">
            {filtered.map((paper) => (
              <tr key={paper.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                <td className="py-4 px-4">
                  <div>
                    <span className="font-bold text-slate-900 dark:text-white block">{paper.subject_name}</span>
                    <span className="font-mono text-xs text-slate-500 dark:text-slate-400">{paper.subject_code}</span>
                  </div>
                </td>
                <td className="py-4 px-4 font-mono text-xs text-slate-700 dark:text-slate-300">
                  <div className="flex items-center gap-1.5">
                    <FileText className="w-4 h-4 text-slate-400" />
                    <span>{paper.original_filename}</span>
                  </div>
                </td>
                <td className="py-4 px-4 font-medium text-slate-700 dark:text-slate-300">{paper.examination_type}</td>
                <td className="py-4 px-4 font-mono text-xs text-slate-500 dark:text-slate-400">
                  {formatDate(paper.upload_timestamp)}
                </td>
                <td className="py-4 px-4">
                  <Badge variant="success" size="sm" className="font-mono">
                    {paper.processing_status}
                  </Badge>
                </td>
                <td className="py-4 px-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/analysis/${paper.id}`)}
                      rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                    >
                      View Results
                    </Button>
                    {onDeletePaper && (
                      <button
                        type="button"
                        onClick={() => setDeletingPaperId(paper.id)}
                        className="p-2 rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                        title="Delete Question Paper"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Delete Confirmation Modal */}
      {deletingPaperId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-md w-full space-y-4 shadow-xl">
            <div className="flex items-center gap-3 text-rose-600 dark:text-rose-400">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Delete Question Paper</h3>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-sans">
              Are you sure you want to delete this question paper? This will permanently remove the paper, all extracted questions, topics, similarity records, and stored files from the backend database.
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <Button variant="ghost" size="sm" onClick={() => setDeletingPaperId(null)}>
                Cancel
              </Button>

              <button
                type="button"
                onClick={confirmDelete}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs rounded-xl transition-colors shadow-xs"
              >
                Delete Permanently
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
