import React from 'react';
import { FileText, Image, Link as LinkIcon, Sparkles, Network, BarChart3, Verified, BookOpen, Search, Moon, History } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-surface via-surface-container-low to-slate-100">
      <main className="pt-24 pb-12 max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Left Content: Hero & Input */}
        <div className="lg:col-span-8 space-y-12">
          {/* Hero Section */}
          <section className="space-y-4">
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/5 border border-primary/10 text-primary text-xs font-bold tracking-widest uppercase mb-4">
              Powered by Veracity Engine v1.0
            </div>
            <h1 className="text-5xl md:text-6xl font-black tracking-tight text-on-surface leading-[1.1]">
              Think Before You <span className="text-primary italic">Believe</span>
            </h1>
            <p className="text-xl text-secondary max-w-2xl leading-relaxed">
              In an era of synthetic misinformation, Forensic Editorial provides the technical rigor of investigative journalism to every citizen. Verify text, images, and links in real-time.
            </p>
          </section>

          {/* Core Interaction Card */}
          <div className="bg-surface-container-lowest rounded-2xl shadow-[0_20px_40px_-12px_rgba(11,28,48,0.06)] border border-outline-variant/15 overflow-hidden">
            {/* Tabs */}
            <div className="flex border-b border-outline-variant/10">
              <button className="flex-1 py-4 px-6 flex items-center justify-center gap-2 border-b-2 border-primary text-primary font-semibold">
                <FileText className="w-5 h-5" />
                Text Input
              </button>
              <button className="flex-1 py-4 px-6 flex items-center justify-center gap-2 text-secondary hover:bg-surface-container-low transition-colors">
                <Image className="w-5 h-5" />
                Image Upload
              </button>
              <button className="flex-1 py-4 px-6 flex items-center justify-center gap-2 text-secondary hover:bg-surface-container-low transition-colors">
                <LinkIcon className="w-5 h-5" />
                URL Input
              </button>
            </div>
            <div className="p-8 space-y-6">
              {/* Text Input Section */}
              <div className="space-y-4">
                <label className="block text-xs font-bold tracking-widest text-secondary uppercase">Analysis Content</label>
                <textarea 
                  className="w-full bg-surface-container-low border border-outline-variant/15 rounded-xl p-6 text-on-surface placeholder:text-secondary/50 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none text-lg leading-relaxed" 
                  placeholder="Paste the suspicious article, social media post, or claim here for a deep forensic audit..." 
                  rows={8}
                />
              </div>
              {/* Action Bar */}
              <div className="flex items-center justify-between pt-4">
                <div className="flex gap-4">
                  <button className="flex items-center gap-2 text-sm font-medium text-secondary hover:text-primary transition-colors">
                    <Sparkles className="w-4 h-4" />
                    Auto-detect Language
                  </button>
                  <button className="flex items-center gap-2 text-sm font-medium text-secondary hover:text-primary transition-colors">
                    <Network className="w-4 h-4" />
                    Context Tuning
                  </button>
                </div>
                <Link to="/dashboard" className="bg-gradient-to-br from-primary to-primary-container text-white px-8 py-4 rounded-xl font-bold text-lg shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center gap-3">
                  <span>Analyze Content</span>
                  <BarChart3 className="w-5 h-5" />
                </Link>
              </div>
            </div>
          </div>

          {/* Feature Teasers */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-8 rounded-2xl bg-tertiary/5 border border-tertiary/10 space-y-3">
              <div className="h-10 w-10 rounded-lg bg-tertiary flex items-center justify-center text-white">
                <Verified className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-on-surface">Linguistic Forensics</h3>
              <p className="text-secondary leading-relaxed">Our models detect synthetic syntactic patterns and emotional manipulation typical of AI-generated misinformation.</p>
            </div>
            <div className="p-8 rounded-2xl bg-primary/5 border border-primary/10 space-y-3">
              <div className="h-10 w-10 rounded-lg bg-primary flex items-center justify-center text-white">
                <BookOpen className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-on-surface">Source Origin Audit</h3>
              <p className="text-secondary leading-relaxed">Cross-reference claims against a decentralized database of verified journalistic outputs and public records.</p>
            </div>
          </div>
        </div>

        {/* Right Content: Recent Analysis Sidebar */}
        <aside className="lg:col-span-4 space-y-8">
          <div className="bg-surface-container-low rounded-2xl p-6 border border-outline-variant/10 h-fit sticky top-24">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-on-surface">Recent Analysis</h2>
              <button className="text-primary text-xs font-bold uppercase tracking-widest hover:underline">View All</button>
            </div>
            <div className="space-y-4">
              {/* History Item 1 */}
              <div className="p-4 bg-surface-container-lowest rounded-xl border border-outline-variant/10 hover:shadow-md transition-shadow group cursor-pointer">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded bg-tertiary/10 text-tertiary">Verified True</span>
                  <span className="text-[10px] text-secondary font-medium">2m ago</span>
                </div>
                <h4 className="text-sm font-bold text-on-surface line-clamp-2 mb-1 group-hover:text-primary transition-colors">Economic Policy Update: Q3 2024 projections and fiscal...</h4>
                <div className="flex items-center gap-2">
                  <LinkIcon className="w-3 h-3 text-secondary" />
                  <span className="text-[10px] text-secondary truncate">bloomberg.com/news/econom...</span>
                </div>
              </div>
              {/* History Item 2 */}
              <div className="p-4 bg-surface-container-lowest rounded-xl border border-outline-variant/10 hover:shadow-md transition-shadow group cursor-pointer">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded bg-error/10 text-error">Likely Fabricated</span>
                  <span className="text-[10px] text-secondary font-medium">1h ago</span>
                </div>
                <h4 className="text-sm font-bold text-on-surface line-clamp-2 mb-1 group-hover:text-primary transition-colors">Emergency health advisory regarding tap water in major...</h4>
                <div className="flex items-center gap-2">
                  <FileText className="w-3 h-3 text-secondary" />
                  <span className="text-[10px] text-secondary truncate">Uploaded Text Snippet</span>
                </div>
              </div>
            </div>
            {/* Trust Stats */}
            <div className="mt-8 pt-6 border-t border-outline-variant/10">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-secondary uppercase tracking-tighter">Community Confidence</span>
                <span className="text-xs font-black text-tertiary">98.4%</span>
              </div>
              <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden flex">
                <div className="h-full bg-tertiary w-[98.4%]"></div>
              </div>
              <p className="text-[11px] text-secondary mt-3 leading-relaxed">
                Forensic Editorial’s Veracity Engine has identified over 1.2M synthetic narratives this month.
              </p>
            </div>
          </div>
          {/* CTA Banner */}
          <div className="relative overflow-hidden rounded-2xl bg-indigo-900 p-8 text-white shadow-xl">
            <div className="relative z-10 space-y-4">
              <h3 className="text-lg font-bold">Editorial Enterprise</h3>
              <p className="text-sm text-indigo-200">Integrate our API into your newsroom or moderation platform.</p>
              <button className="w-full bg-white text-indigo-900 py-2.5 rounded-lg font-bold text-sm hover:bg-indigo-50 transition-colors">
                Request Access
              </button>
            </div>
            <div className="absolute -right-12 -bottom-12 w-48 h-48 bg-white/5 rounded-full blur-2xl"></div>
          </div>
        </aside>
      </main>
      <footer className="bg-surface border-t border-outline-variant/5 py-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="text-sm text-secondary">
            © 2024 Forensic Editorial. All investigative rights reserved.
          </div>
          <div className="flex gap-8 text-xs font-bold text-secondary uppercase tracking-widest">
            <a className="hover:text-primary transition-colors" href="#">Privacy Protocol</a>
            <a className="hover:text-primary transition-colors" href="#">Terms of Service</a>
            <a className="hover:text-primary transition-colors" href="#">Trust Report</a>
            <a className="hover:text-primary transition-colors" href="#">API Status</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
