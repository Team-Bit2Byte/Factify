import React from 'react';
import { AlertTriangle, Share, Download, ClipboardCheck, XCircle, FileText, Image, ShieldCheck, ArrowRight, Brain, Verified, ArrowLeftRight, Shield } from 'lucide-react';

export default function AnalysisReport() {
  return (
    <div className="w-full h-full bg-surface-container-lowest/50 backdrop-blur-xl rounded-3xl p-6 md:p-8 shadow-sm border border-outline-variant/15 animate-in fade-in slide-in-from-right-8 duration-700">
      {/* Header Section */}
      <section className="flex flex-col md:flex-row justify-between items-start gap-8 mb-12">
        <div className="space-y-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-error-container text-error text-[10px] font-bold uppercase tracking-widest">
            <AlertTriangle className="w-3 h-3 fill-current" />
            Likely Fake
          </span>
          <h1 className="text-3xl lg:text-5xl font-black tracking-tight text-on-surface leading-tight max-w-2xl">
            Global Energy Shortage: The Hidden Narrative Revealed
          </h1>
          <p className="text-secondary font-medium flex items-center gap-2 text-sm">
            Analysed on Oct 24, 2023 • <span className="text-on-surface">Article ID: 4920-X1</span>
          </p>
        </div>
        <div className="flex gap-3 shrink-0">
          <button 
            onClick={() => alert('Share dialog coming soon!')}
            className="flex items-center gap-2 px-4 py-2 bg-surface-container-highest text-on-surface rounded-lg font-bold text-sm hover:bg-surface-variant transition-colors"
          >
            <Share className="w-4 h-4" />
            Share
          </button>
          <button 
            onClick={() => alert('PDF export started!')}
            className="flex items-center gap-2 px-4 py-2 bg-surface-container-highest text-on-surface rounded-lg font-bold text-sm hover:bg-surface-variant transition-colors"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </section>

      {/* Top Bento Grid: Score & Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
        {/* Score Display (4/12) */}
        <div className="lg:col-span-4 bg-white rounded-3xl p-8 flex flex-col items-center justify-center text-center shadow-sm border border-outline-variant/10 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4">
            <span className="flex items-center gap-1 text-tertiary font-bold text-xs bg-tertiary-fixed-dim/30 px-2 py-1 rounded-full">
              Confidence: High
            </span>
          </div>
          <div className="relative w-48 h-48 mb-6 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle className="text-surface-container" cx="50" cy="50" fill="transparent" r="44" stroke="currentColor" strokeWidth="8"></circle>
              <circle className="text-error transition-all duration-1000" cx="50" cy="50" fill="transparent" r="44" stroke="currentColor" strokeDasharray="276" strokeDashoffset="50" strokeLinecap="round" strokeWidth="8"></circle>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-5xl font-black text-on-surface leading-none">82%</span>
              <span className="text-xs uppercase tracking-widest text-secondary mt-1 font-bold">Probability</span>
            </div>
          </div>
          <h3 className="text-xl font-bold text-on-surface mb-2">Fake News Detected</h3>
          <p className="text-sm text-secondary leading-relaxed">Highly correlated with known misinformation patterns in geopolitical reporting.</p>
        </div>

        {/* Explanation Panel (8/12) */}
        <div className="lg:col-span-8 bg-surface-container-low rounded-3xl p-8 flex flex-col">
          <div className="flex items-center gap-2 mb-6">
            <ClipboardCheck className="text-primary w-6 h-6" />
            <h2 className="text-xl font-bold">Veracity Verdict</h2>
          </div>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 h-full">
            <div className="space-y-4">
              <h4 className="text-sm font-bold uppercase tracking-wider text-secondary">Key Findings</h4>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <XCircle className="text-error w-5 h-5 fill-current shrink-0" />
                  <p className="text-sm font-medium">Emotionally exaggerated language designed to trigger fear.</p>
                </li>
                <li className="flex items-start gap-3">
                  <XCircle className="text-error w-5 h-5 fill-current shrink-0" />
                  <p className="text-sm font-medium">Low credibility source domain with history of retracted claims.</p>
                </li>
                <li className="flex items-start gap-3">
                  <XCircle className="text-error w-5 h-5 fill-current shrink-0" />
                  <p className="text-sm font-medium">Inconsistent metadata timestamps in the accompanying media.</p>
                </li>
              </ul>
            </div>
            <div className="bg-white/50 rounded-2xl p-6 border border-white/80">
              <h4 className="text-sm font-bold uppercase tracking-wider text-secondary mb-4">Neural Map Breakdown</h4>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs font-bold mb-1.5">
                    <span>Syntax Deviation</span>
                    <span>94%</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-error w-[94%]"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-bold mb-1.5">
                    <span>Semantic Consistency</span>
                    <span>12%</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-error w-[12%]"></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-bold mb-1.5">
                    <span>Authority Alignment</span>
                    <span>08%</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-error w-[8%]"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Detail Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Text Analysis Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-outline-variant/10 group hover:border-primary/20 transition-all">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <FileText className="text-primary w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold mb-2">Text Analysis</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Sentiment</span>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-error-container text-error rounded">Hyper-Negative</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Clickbait</span>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-error-container text-error rounded">9.4 / 10</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-secondary">AI Auth</span>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">Likely (76%)</span>
            </div>
          </div>
        </div>
        {/* Image Analysis Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-outline-variant/10 group hover:border-primary/20 transition-all">
          <div className="w-10 h-10 rounded-xl bg-secondary/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <Image className="text-secondary w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold mb-2">Image Forensics</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Manipulation</span>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-error-container text-error rounded">Detected</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">ELA Result</span>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">High Noise</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-secondary">Origin</span>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">Stock Asset</span>
            </div>
          </div>
        </div>
        {/* Source Credibility Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-outline-variant/10 group hover:border-primary/20 transition-all">
          <div className="w-10 h-10 rounded-xl bg-tertiary/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <ShieldCheck className="text-tertiary w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold mb-2">Domain Trust</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Blacklist Status</span>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-error-container text-error rounded">Flagged</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Age</span>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">14 Days</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-secondary">IP Loc</span>
              <span className="text-[10px] font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">Obfuscated</span>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Visual Evidence */}
      <section className="mt-12">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-black tracking-tight">Visual Forensics</h2>
          <button 
            onClick={() => alert('Full metadata panel coming soon!')}
            className="text-primary font-bold text-sm flex items-center gap-1 hover:underline"
          >
            Full Metadata <ArrowRight className="w-3 h-3" />
          </button>
        </div>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <div className="relative rounded-3xl overflow-hidden aspect-[4/3] shadow-lg">
            <img 
              alt="Digital Manipulation Analysis" 
              className="w-full h-full object-cover"
              src="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=1000"
              referrerPolicy="no-referrer"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent flex items-end p-6">
              <div>
                <h4 className="text-white font-bold text-lg">Compression Anomaly Detected</h4>
                <p className="text-white/80 text-xs">Artificial pixel interpolation suggests generative filling.</p>
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-6">
            <div className="glass-panel p-6 rounded-3xl border border-white/40 flex-1">
              <h4 className="font-bold text-lg mb-4">Neural Comparison</h4>
              <div className="flex gap-4">
                <div className="flex-1 text-center">
                  <div className="bg-surface-container h-24 rounded-xl mb-2 flex items-center justify-center">
                    <Brain className="text-error w-8 h-8" />
                  </div>
                  <span className="text-[10px] font-bold uppercase text-secondary tracking-widest">Target Sample</span>
                </div>
                <div className="flex items-center">
                  <ArrowLeftRight className="text-secondary w-6 h-6" />
                </div>
                <div className="flex-1 text-center">
                  <div className="bg-surface-container h-24 rounded-xl mb-2 flex items-center justify-center">
                    <Verified className="text-primary w-8 h-8" />
                  </div>
                  <span className="text-[10px] font-bold uppercase text-secondary tracking-widest">Verified Baseline</span>
                </div>
              </div>
              <p className="text-xs text-secondary mt-4 italic">"Structural patterns diverge significantly from journalistic standards for this topic."</p>
            </div>
            <div className="bg-on-surface rounded-3xl p-6 text-white flex items-center justify-between">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-white/50 mb-1">Global Verdict Integrity</p>
                <p className="text-2xl font-black">99.8%</p>
              </div>
              <Shield className="w-8 h-8 text-primary-container fill-current" />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
