import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from './Button';

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends React.Component<React.PropsWithChildren, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('Unhandled React component error:', error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div className="min-h-[50vh] flex items-center justify-center p-6">
        <div className="max-w-lg w-full rounded-xl border border-rose-200 dark:border-rose-900 bg-white dark:bg-slate-900 p-6 text-center space-y-4">
          <div className="mx-auto h-10 w-10 rounded-lg bg-rose-50 dark:bg-rose-950/60 flex items-center justify-center">
            <AlertTriangle className="h-5 w-5 text-rose-600 dark:text-rose-400" />
          </div>
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Something went wrong</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              This view could not be rendered. Refreshing will restart the interface.
            </p>
          </div>
          <Button type="button" variant="primary" onClick={() => window.location.reload()}>
            Refresh
          </Button>
        </div>
      </div>
    );
  }
}
