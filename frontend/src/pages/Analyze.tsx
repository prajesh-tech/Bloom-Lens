import React, { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Dropzone } from '../components/upload/Dropzone';
import { FilePreview } from '../components/upload/FilePreview';
import { ProcessingProgress } from '../components/upload/ProcessingProgress';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { toast } from '../components/common/Toast';
import { Sparkles, AlertCircle } from 'lucide-react';
import { useUploadPaperMutation, usePaperStatusQuery } from '../services/queries';

export const Analyze: React.FC = () => {
  const navigate = useNavigate();
  const uploadPaper = useUploadPaperMutation();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [subjectCode, setSubjectCode] = useState('');
  const [subjectName, setSubjectName] = useState('');
  const [examType, setExamType] = useState('End-Semester');
  const [maxMarks, setMaxMarks] = useState<number>(100);
  const [yearDate, setYearDate] = useState('');

  const [pendingPaperId, setPendingPaperId] = useState<number>();
  const paperStatus = usePaperStatusQuery(pendingPaperId);
  const queryClient = useQueryClient();
  const isProcessing = uploadPaper.isPending || pendingPaperId !== undefined;
  const currentStep = paperStatus.data?.processing_status === 'ANALYZING' ? 3
    : paperStatus.data?.processing_status === 'PROCESSING' ? 2 : 1;

  useEffect(() => {
    if (pendingPaperId === undefined) return;
    const status = paperStatus.data;
    if (status?.processing_status === 'COMPLETED' || status?.processing_status === 'REVIEW_REQUIRED') {
      queryClient.invalidateQueries({ queryKey: ['papers'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
      setPendingPaperId(undefined);
      toast.success('Question paper analyzed successfully!');
      navigate(`/analysis/${pendingPaperId}`);
    } else if (status?.processing_status === 'FAILED') {
      toast.error(status.error_message || status.message);
      setPendingPaperId(undefined);
    }
  }, [paperStatus.data, pendingPaperId, queryClient, navigate]);

  const handleStartAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      toast.error('Please select a PDF or DOCX file.');
      return;
    }
    if (!subjectCode.trim() || !subjectName.trim()) {
      toast.error('Please fill in Subject Code and Subject Name.');
      return;
    }
    if (!maxMarks || maxMarks <= 0) {
      toast.error('Maximum paper marks must be greater than 0.');
      return;
    }

    try {
      const paper = await uploadPaper.mutateAsync({
        subject_code: subjectCode.trim(),
        subject_name: subjectName.trim(),
        examination_type: examType,
        maximum_marks: maxMarks,
        year_date: yearDate.trim() || undefined,
        file: selectedFile,
      });

      setPendingPaperId(paper.id);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Unable to upload the document. Please try again.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in">
      {/* Page Title */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Analyze Question Paper
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-mono max-w-xl mx-auto">
          Upload a PDF or DOCX question paper to automatically extract questions, compute Revised Bloom’s Taxonomy cognitive levels, and evaluate paper marks distribution.
        </p>
      </div>

      {isProcessing ? (
        <div>
          <ProcessingProgress currentStep={currentStep} />
          {paperStatus.isError && <div role="alert">Unable to check progress.
            <Button onClick={() => paperStatus.refetch()}>Retry status check</Button>
          </div>}
        </div>
      ) : (
        <form onSubmit={handleStartAnalysis} className="space-y-6">
          {!selectedFile ? (
            <Dropzone onFileSelect={(file) => setSelectedFile(file)} />
          ) : (
            <FilePreview
              file={selectedFile}
              subjectCode={subjectCode}
              setSubjectCode={setSubjectCode}
              subjectName={subjectName}
              setSubjectName={setSubjectName}
              examType={examType}
              setExamType={setExamType}
              maxMarks={maxMarks}
              setMaxMarks={setMaxMarks}
              yearDate={yearDate}
              setYearDate={setYearDate}
              onRemove={() => setSelectedFile(null)}
            />
          )}

          {selectedFile && (
            <div className="flex justify-end gap-3 pt-2">
              <Button variant="ghost" type="button" onClick={() => setSelectedFile(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                type="submit"
                size="lg"
                leftIcon={<Sparkles className="w-5 h-5 text-sky-400" />}
                isLoading={uploadPaper.isPending}
              >
                Run BloomLens Analysis
              </Button>
            </div>
          )}
        </form>
      )}

      {/* Info Callout */}
      <Card className="bg-slate-100/60 dark:bg-slate-800/50 border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300 space-y-1">
        <div className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
          <AlertCircle className="w-4 h-4 text-slate-500 dark:text-slate-400" /> Supported Question Formats
        </div>
        <p className="leading-relaxed font-sans">
          Supports text PDFs, scanned PDFs (via PaddleOCR), and DOCX files. Automatically recognizes main questions (Q1, Q2) and sub-questions (Q1a, Q1b), marks, and Bloom cognitive levels (L1 Remember to L6 Create).
        </p>
      </Card>
    </div>
  );
};
