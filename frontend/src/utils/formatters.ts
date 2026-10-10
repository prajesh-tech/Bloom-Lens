/**
 * Formats question marks e.g., 5 -> "05 marks", 2.5 -> "2.5 marks", null -> "—"
 * Only single-digit integers (1–9) get a leading zero; floats are never padded.
 */
export function formatMarks(marks?: number | null): string {
  if (marks === undefined || marks === null) return '—';
  const isWholeNumber = Number.isInteger(marks);
  const rounded = isWholeNumber ? marks : marks.toFixed(1);
  const padded = isWholeNumber && marks >= 1 && marks < 10 ? `0${rounded}` : `${rounded}`;
  return `${padded} marks`;
}

/**
 * Formats confidence decimal e.g. 0.942 -> "94%"
 */
export function formatConfidence(confidence?: number | null): string {
  if (confidence === undefined || confidence === null) return '—';
  const pct = Math.round(confidence > 1 ? confidence : confidence * 100);
  return `${pct}%`;
}

/**
 * Formats Question ID / Number e.g. 1 -> "Q01", "Q1(a)" -> "Q01(a)"
 */
export function formatQuestionId(qNum: string | number): string {
  const str = String(qNum).trim();
  if (/^\d+$/.test(str)) {
    const num = parseInt(str, 10);
    return num < 10 ? `Q0${num}` : `Q${num}`;
  }
  if (/^Q\d+/i.test(str)) {
    return str.replace(/^Q(\d+)/i, (_, num) => {
      const n = parseInt(num, 10);
      return n < 10 ? `Q0${n}` : `Q${n}`;
    });
  }
  return str;
}

/**
 * Formats bytes to human-readable string (e.g. 2400000 -> "2.4 MB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Formats ISO date string
 */
export function formatDate(dateString?: string): string {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
}
