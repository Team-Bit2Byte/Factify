import React from 'react';
import { AlertTriangle, Share2, Download } from 'lucide-react';

export function AnalysisHeader() {
  return (
    <section className="flex flex-col md:flex-row justify-between items-start gap-8 mb-12">
      <div className="space-y-2">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-error-container text-error text-[10px] font-bold uppercase tracking-widest">
          <AlertTriangle className="w-3 h-3 fill-current" />
          Likely Fake
        </span>
        <h1 className="text-4xl md:text-5xl font-black tracking-tight text-on-surface leading-tight max-w-2xl">
          Global Energy Shortage: The Hidden Narrative Revealed
        </h1>
        <p className="text-secondary font-medium flex items-center gap-2">
          Analysed on Oct 24, 2023 • <span className="text-on-surface">Article ID: 4920-X1</span>
        </p>
      </div>
      <div className="flex gap-3">
        <button className="flex items-center gap-2 px-5 py-2.5 bg-surface-container-highest text-on-surface rounded-lg font-bold text-sm hover:bg-surface-container-high transition-colors">
          <Share2 className="w-4 h-4" />
          Share
        </button>
        <button className="flex items-center gap-2 px-5 py-2.5 bg-surface-container-highest text-on-surface rounded-lg font-bold text-sm hover:bg-surface-container-high transition-colors">
          <Download className="w-4 h-4" />
          Export PDF
        </button>
      </div>
    </section>
  );
}
