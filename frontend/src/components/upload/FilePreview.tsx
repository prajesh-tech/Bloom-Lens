import React from 'react';
import { X } from 'lucide-react';
import { formatFileSize } from '../../utils/formatters';
import { SUPPORTED_EXAM_TYPES } from '../../config/constants';

interface FilePreviewProps {
  file: File;
  subjectCode: string;
  setSubjectCode: (val: string) => void;
  subjectName: string;
  setSubjectName: (val: string) => void;
  examType: string;
  setExamType: (val: string) => void;
  maxMarks: number;
  setMaxMarks: (val: number) => void;
  yearDate: string;
  setYearDate: (val: string) => void;
  onRemove: () => void;
}

export const FilePreview: React.FC<FilePreviewProps> = ({
  file,
  subjectCode,
  setSubjectCode,
  subjectName,
  setSubjectName,
  examType,
  setExamType,
  maxMarks,
  setMaxMarks,
  yearDate,
  setYearDate,
  onRemove,
}) => {
  const ext = file.name.split('.').pop()?.toUpperCase() || 'FILE';

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-6 transition-colors">
      {/* File Card Header */}
      <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-lg bg-slate-900 dark:bg-sky-950 text-white flex items-center justify-center font-bold text-xs font-mono flex-shrink-0">
            {ext}
          </div>
          <div className="truncate">
            <h4 className="text-sm font-bold text-slate-900 dark:text-white truncate">{file.name}</h4>
            <p className="text-xs font-mono text-slate-500 dark:text-slate-400">{formatFileSize(file.size)}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onRemove}
          className="p-1.5 rounded-lg text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/80 dark:hover:bg-slate-700 transition-colors"
          title="Remove file"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Metadata Form Inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Subject Code <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            required
            placeholder="e.g. CS301"
            value={subjectCode}
            onChange={(e) => setSubjectCode(e.target.value)}
            className="w-full px-3 py-2 text-sm font-mono bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Subject Name <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            required
            placeholder="e.g. Database Management Systems"
            value={subjectName}
            onChange={(e) => setSubjectName(e.target.value)}
            className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Examination Type <span className="text-rose-500">*</span>
          </label>
          <select
            value={examType}
            onChange={(e) => setExamType(e.target.value)}
            className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600"
          >
            {SUPPORTED_EXAM_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Maximum Paper Marks <span className="text-rose-500">*</span>
          </label>
          <input
            type="number"
            required
            min="1"
            placeholder="100"
            value={maxMarks || ''}
            onChange={(e) => setMaxMarks(parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 text-sm font-mono bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600"
          />
        </div>

        <div className="sm:col-span-2">
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Year / Date (Optional)
          </label>
          <input
            type="text"
            placeholder="e.g. May 2024 or 2023-2024"
            value={yearDate}
            onChange={(e) => setYearDate(e.target.value)}
            className="w-full px-3 py-2 text-sm font-mono bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600"
          />
        </div>
      </div>
    </div>
  );
};
