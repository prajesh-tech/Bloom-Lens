import React, { useState, useRef } from 'react';
import { UploadCloud, FileText } from 'lucide-react';
import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES } from '../../config/constants';
import { toast } from '../common/Toast';

interface DropzoneProps {
  onFileSelect: (file: File) => void;
}

export const Dropzone: React.FC<DropzoneProps> = ({ onFileSelect }) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_FILE_TYPES.includes(ext)) {
      toast.error('Please upload a valid PDF or DOCX question paper file.');
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      toast.error(`File size exceeds maximum limit of ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    onFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndSelect(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSelect(e.target.files[0]);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
      className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
        isDragging
          ? 'border-sky-500 bg-sky-50/50 dark:bg-slate-800 scale-[1.01]'
          : 'border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600 bg-white dark:bg-slate-900 hover:bg-slate-50/50 dark:hover:bg-slate-800/50 shadow-xs'
      }`}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx"
        className="hidden"
        onChange={handleFileInputChange}
      />

      <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-100 dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-200 shadow-xs">
        <UploadCloud className="w-8 h-8 text-slate-700 dark:text-slate-300" />
      </div>

      <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
        Upload Question Paper
      </h3>
      <p className="text-sm text-slate-500 dark:text-slate-400 mb-4 max-w-sm mx-auto">
        Drag and drop your examination question paper here, or click to browse.
      </p>

      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-mono text-slate-600 dark:text-slate-300">
        <FileText className="w-3.5 h-3.5" />
        <span>PDF, DOCX (Max {MAX_FILE_SIZE_MB}MB)</span>
      </div>
    </div>
  );
};
