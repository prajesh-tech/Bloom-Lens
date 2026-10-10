import React from 'react';
import { QuestionPaper } from '../../types/paper';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { Download, Calendar, FileCheck, ArrowLeft, Printer } from 'lucide-react';
import { formatDate } from '../../utils/formatters';
import { useNavigate } from 'react-router-dom';
import { toast } from '../common/Toast';
import { QuestionAnalysis } from '../../types/question';

interface AnalysisHeaderProps {
  paper: QuestionPaper;
  questions: QuestionAnalysis[];
}

export const AnalysisHeader: React.FC<AnalysisHeaderProps> = ({ paper, questions }) => {
  const navigate = useNavigate();

  const handlePrintPDF = () => {
    window.print();
    toast.success('Print / PDF report export triggered.');
  };

  const handleExportJSON = () => {
    const exportBlob = new Blob([JSON.stringify({ paper, questions }, null, 2)], {
      type: 'application/json',
    });
    const downloadUrl = URL.createObjectURL(exportBlob);
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', downloadUrl);
    downloadAnchor.setAttribute('download', `BloomLens_Report_${paper.subject_code}_${paper.id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    URL.revokeObjectURL(downloadUrl);
    toast.success(`Exported analytical report for ${paper.subject_code}`);
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-6 shadow-xs space-y-4 transition-colors">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <button
            type="button"
            onClick={() => navigate('/history')}
            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors mb-1 print:hidden"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to History
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
              {paper.subject_name}
            </h1>
            <Badge variant="primary" className="font-mono">
              {paper.subject_code}
            </Badge>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400 font-mono pt-1">
            <span className="flex items-center gap-1">
              <FileCheck className="w-3.5 h-3.5 text-slate-400" />
              {paper.original_filename}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              Uploaded {formatDate(paper.upload_timestamp)}
            </span>
            <span>•</span>
            <span className="font-semibold text-slate-800 dark:text-slate-200">{paper.examination_type}</span>
          </div>
        </div>

        {/* Actions (Hidden during print) */}
        <div className="flex items-center gap-2 print:hidden">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrintPDF}
            leftIcon={<Printer className="w-4 h-4" />}
          >
            Print / Save PDF
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleExportJSON}
            leftIcon={<Download className="w-4 h-4" />}
          >
            Export JSON
          </Button>
        </div>
      </div>
    </div>
  );
};
