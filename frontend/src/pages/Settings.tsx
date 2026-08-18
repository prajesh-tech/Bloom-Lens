import React from 'react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { BLOOM_CONFIG } from '../config/bloomConfig';
import { Settings as SettingsIcon, Server, Shield, Layers } from 'lucide-react';

export const Settings: React.FC = () => {
  const isMock = import.meta.env.VITE_USE_MOCK_API !== 'false';
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-slate-900 dark:bg-sky-950 text-white flex items-center justify-center shadow-xs">
          <SettingsIcon className="w-5 h-5 text-sky-400" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Application Settings
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
            Environment configuration and Bloom Taxonomy design tokens
          </p>
        </div>
      </div>

      {/* Backend API Configuration */}
      <Card className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-slate-700 dark:text-slate-300" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">API Service Configuration</h3>
          </div>
          {isMock ? (
            <Badge variant="warning" className="font-mono">
              ⚡ Mock API Mode Active
            </Badge>
          ) : (
            <Badge variant="success" className="font-mono">
              ● FastAPI Backend Connected
            </Badge>
          )}
        </div>

        <div className="space-y-3 text-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800">
            <span className="font-semibold text-slate-700 dark:text-slate-300">API Base URL (VITE_API_BASE_URL)</span>
            <code className="font-mono text-xs text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-900 px-2.5 py-1 rounded border border-slate-300 dark:border-slate-700">
              {apiBaseUrl}
            </code>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800">
            <span className="font-semibold text-slate-700 dark:text-slate-300">Mock Network Latency Simulation</span>
            <span className="font-mono text-xs text-slate-700 dark:text-slate-300 font-bold">1500ms – 2500ms random delay</span>
          </div>
        </div>
      </Card>

      {/* Bloom Taxonomy System Tokens */}
      <Card className="space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
          <Layers className="w-5 h-5 text-slate-700 dark:text-slate-300" />
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Centralized Bloom Taxonomy Tokens</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(BLOOM_CONFIG).map(([key, item]) => (
            <div key={key} className={`p-4 rounded-xl border ${item.bgClass} ${item.borderClass} space-y-2`}>
              <div className="flex items-center justify-between">
                <span className={`font-bold text-sm ${item.textClass}`}>{item.label}</span>
                <span className="font-mono text-xs font-bold text-slate-600 dark:text-slate-400">[{item.code}]</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-tight">{item.description}</p>
              <div className="flex flex-wrap gap-1 pt-1">
                {item.verbs.map((v) => (
                  <span key={v} className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-900 text-[10px] font-mono text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                    {v}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Privacy & Security */}
      <Card className="space-y-2 bg-slate-100/60 dark:bg-slate-800/50 border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300">
        <div className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
          <Shield className="w-4 h-4 text-slate-500 dark:text-slate-400" /> Security Notice
        </div>
        <p className="leading-relaxed">
          Client-side environment variables prefixed with <code className="font-mono bg-white dark:bg-slate-900 px-1 py-0.5 rounded border dark:border-slate-700">VITE_</code> are exposed to browser execution and contain no backend secrets or API keys.
        </p>
      </Card>
    </div>
  );
};
