import React, { useState, useEffect } from 'react';
import { QuestionAnalysis, QuestionPatchPayload } from '../../types/question';
import { Drawer } from '../common/Drawer';
import { BloomBadge } from '../common/BloomBadge';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { formatMarks, formatConfidence, formatQuestionId } from '../../utils/formatters';
import { BLOOM_CONFIG, getBloomCode, getBloomConfig } from '../../config/bloomConfig';
import { Copy, Edit3, Check, AlertTriangle, Sparkles } from 'lucide-react';
import { toast } from '../common/Toast';

interface QuestionDrawerProps {
  question: QuestionAnalysis | null;
  isOpen: boolean;
  onClose: () => void;
  onSaveOverride: (questionId: number, payload: QuestionPatchPayload) => Promise<void>;
}

export const QuestionDrawer: React.FC<QuestionDrawerProps> = ({
  question,
  isOpen,
  onClose,
  onSaveOverride,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [copied, setCopied] = useState(false);

  // Form State for Human Override
  const [editText, setEditText] = useState('');
  const [editMarks, setEditMarks] = useState<number | ''>('');
  const [editBloom, setEditBloom] = useState('');
  const [editTopic, setEditTopic] = useState('');
  const [editUnit, setEditUnit] = useState('');
  const [editType, setEditType] = useState('');

  useEffect(() => {
    if (question) {
      setEditText(question.original_text);
      setEditMarks(question.marks ?? '');
      // Normalize Bloom level to label name (e.g. 'L1' -> 'Remember') so the select populates correctly
      const rawBloom = question.effective_bloom_level || question.ai_bloom_level || 'Remember';
      const normalizedBloom = getBloomConfig(rawBloom).label;
      setEditBloom(normalizedBloom);
      setEditTopic(question.topic || '');
      setEditUnit(question.unit || '');
      setEditType(question.question_type || 'Descriptive');
      setIsEditing(false);
    }
  }, [question]);

  if (!question) return null;

  const effectiveLvl = question.effective_bloom_level || question.ai_bloom_level;
  const meta = question.ai_analysis_metadata;
  const isLowConfidence = question.bloom_confidence !== null && question.bloom_confidence !== undefined && question.bloom_confidence < 0.70;

  const handleCopyText = () => {
    navigator.clipboard.writeText(question.original_text);
    setCopied(true);
    toast.success('Question copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const bloomCode = getBloomCode(editBloom);
      if (!bloomCode) {
        throw new Error('Please select a valid Bloom level.');
      }

      await onSaveOverride(question.id, {
        question_text: editText,
        marks: editMarks === '' ? undefined : Number(editMarks),
        bloom_level: bloomCode,
        topic_name: editTopic || undefined,
        unit: editUnit || undefined,
        question_type: editType || undefined,
      });
      toast.success('Human classification override saved successfully');
      setIsEditing(false);
    } catch (err: any) {
      toast.error(err.message || 'Failed to save correction');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={`Question ${formatQuestionId(question.question_number)}`}
      subtitle={`Analysis Record ID: #${question.id}`}
    >
      {/* Top Action Bar */}
      <div className="flex items-center justify-between gap-3 pb-2">
        <div className="flex items-center gap-2">
          <BloomBadge level={effectiveLvl} size="lg" />
          {question.review_status === 'CORRECTED' && (
            <Badge variant="primary" size="sm" className="font-mono">
              Human Overridden
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopyText}
            leftIcon={copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          >
            {copied ? 'Copied' : 'Copy Text'}
          </Button>
          {!isEditing && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsEditing(true)}
              leftIcon={<Edit3 className="w-3.5 h-3.5" />}
            >
              Override
            </Button>
          )}
        </div>
      </div>

      {/* Low Confidence Warning Alert */}
      {isLowConfidence && (
        <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <strong className="font-semibold block mb-0.5">Low Classification Confidence</strong>
            <span>AI Bloom classification confidence is {formatConfidence(question.bloom_confidence)}. Manual review is recommended.</span>
          </div>
        </div>
      )}

      {/* Main Question Text Block */}
      {!isEditing ? (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Question Text</h4>
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-900 dark:text-slate-100 leading-relaxed whitespace-pre-wrap">
            {question.original_text}
          </div>
        </div>
      ) : (
        /* Human Override Form */
        <form onSubmit={handleSave} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
            <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
              <Edit3 className="w-4 h-4 text-slate-700 dark:text-slate-300" /> Human Override Form
            </h4>
            <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">AI prediction will be preserved</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Question Text</label>
            <textarea
              rows={3}
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Marks</label>
              <input
                type="number"
                value={editMarks}
                onChange={(e) => setEditMarks(e.target.value ? Number(e.target.value) : '')}
                className="w-full px-3 py-1.5 text-sm font-mono bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Bloom Level</label>
              <select
                value={editBloom}
                onChange={(e) => setEditBloom(e.target.value)}
                className="w-full px-3 py-1.5 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600 font-semibold"
              >
                {Object.keys(BLOOM_CONFIG).map((lbl) => (
                  <option key={lbl} value={lbl} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
                    {lbl}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Topic Name</label>
              <input
                type="text"
                value={editTopic}
                onChange={(e) => setEditTopic(e.target.value)}
                className="w-full px-3 py-1.5 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Unit</label>
              <input
                type="text"
                value={editUnit}
                onChange={(e) => setEditUnit(e.target.value)}
                className="w-full px-3 py-1.5 text-sm font-mono bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Question Type</label>
              <select
                value={editType}
                onChange={(e) => setEditType(e.target.value)}
                className="w-full px-3 py-1.5 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600"
              >
                {['Descriptive', 'Numerical', 'MCQ', 'Short Answer', 'Diagram', 'Case Study'].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-700">
            <Button variant="ghost" size="sm" type="button" onClick={() => setIsEditing(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isSaving}>
              Save Correction
            </Button>
          </div>
        </form>
      )}

      {/* Core Question Analytical Metadata Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700 space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Assigned Marks</span>
          <span className="text-base font-bold font-mono text-slate-900 dark:text-white">{formatMarks(question.marks)}</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700 space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Classification Confidence</span>
          <span className="text-base font-bold font-mono text-slate-900 dark:text-white">{formatConfidence(question.bloom_confidence)}</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700 space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Question Category</span>
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">{question.question_type || 'Descriptive'}</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700 space-y-1">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">Identified Unit</span>
          <span className="text-sm font-mono font-semibold text-slate-800 dark:text-slate-200">{question.unit || 'Not Identified'}</span>
        </div>
      </div>

      {/* AI Explanation & Reasoning Block */}
      <div className="p-4 rounded-xl bg-slate-900 dark:bg-slate-950 border border-slate-800 text-white space-y-2">
        <div className="flex items-center gap-2 text-sky-400 font-semibold text-xs uppercase tracking-wider">
          <Sparkles className="w-4 h-4" />
          <span>AI Bloom Classification Reasoning</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed font-sans">
          {question.bloom_explanation || 'Cognitive task evaluated across hybrid verb, semantic, and structure signals.'}
        </p>
      </div>

      {/* Detailed Signal Scores */}
      {meta && (
        <div className="space-y-3">
        <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Component Signal Scores</h4>
          <div className="space-y-2">
            {meta.cognitive_operation && (
              <div className="text-xs p-3 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300">
                <strong className="text-slate-900 dark:text-white block mb-0.5">Cognitive Task:</strong> {meta.cognitive_operation}
              </div>
            )}
            {meta.detected_verbs && meta.detected_verbs.length > 0 && (
              <div className="text-xs p-3 rounded-lg bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300">
                <strong className="text-slate-900 dark:text-white block mb-0.5">Detected Action Verbs:</strong>
                <div className="flex flex-wrap gap-1 mt-1">
                  {meta.detected_verbs.map((v) => (
                    <span key={v} className="px-2 py-0.5 rounded bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 font-mono text-[11px] text-slate-700 dark:text-slate-300">
                      {v}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </Drawer>
  );
};
