import React, { useState } from 'react';
import { FileText, Image, Link as LinkIcon, Sparkles, Network, BarChart3, Verified, BookOpen, Search, Moon, History, UploadCloud } from 'lucide-react';
import { Link } from 'react-router-dom';
import AnalysisReport from '../components/dashboard/AnalysisReport';

export default function LandingPage() {
  const [activeTab, setActiveTab] = useState<'text' | 'image' | 'url'>('text');
  const [showAnalysis, setShowAnalysis] = useState(false);
  return (
    <div className="min-h-screen bg-gradient-to-b from-surface via-surface-container-low to-slate-100">
      <main className={`pt-24 pb-12 mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 transition-all duration-700 ${showAnalysis ? 'max-w-[1700px] w-full' : 'max-w-4xl'}`}>
        {/* Left Content: Hero & Input */}
        <div className={`space-y-12 transition-all duration-700 ${showAnalysis ? 'lg:col-span-5 xl:col-span-4' : 'lg:col-span-12'}`}>
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
              <button 
                type="button" 
                onClick={() => setActiveTab('text')} 
                className={`flex-1 py-4 px-6 flex items-center justify-center gap-2 transition-colors ${activeTab === 'text' ? 'border-b-2 border-primary text-primary font-semibold' : 'text-secondary hover:bg-surface-container-low'}`}
              >
                <FileText className="w-5 h-5" />
                Text Input
              </button>
              <button 
                type="button" 
                onClick={() => setActiveTab('image')} 
                className={`flex-1 py-4 px-6 flex items-center justify-center gap-2 transition-colors ${activeTab === 'image' ? 'border-b-2 border-primary text-primary font-semibold' : 'text-secondary hover:bg-surface-container-low'}`}
              >
                <Image className="w-5 h-5" />
                Image Upload
              </button>
              <button 
                type="button" 
                onClick={() => setActiveTab('url')} 
                className={`flex-1 py-4 px-6 flex items-center justify-center gap-2 transition-colors ${activeTab === 'url' ? 'border-b-2 border-primary text-primary font-semibold' : 'text-secondary hover:bg-surface-container-low'}`}
              >
                <LinkIcon className="w-5 h-5" />
                URL Input
              </button>
            </div>
            <div className="p-8 space-y-6">
              {/* Input Section */}
              <div className="space-y-4">
                <label className="block text-xs font-bold tracking-widest text-secondary uppercase">Analysis Content</label>
                
                {activeTab === 'text' && (
                  <textarea 
                    className="w-full bg-surface-container-low border border-outline-variant/15 rounded-xl p-6 text-on-surface placeholder:text-secondary/50 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none text-lg leading-relaxed" 
                    placeholder="Paste the suspicious article, social media post, or claim here for a deep forensic audit..." 
                    rows={8}
                  />
                )}

                {activeTab === 'image' && (
                  <div className="w-full h-64 border-2 border-dashed border-outline-variant/30 rounded-xl bg-surface-container-low flex flex-col items-center justify-center text-center p-6 hover:bg-surface-container-high transition-colors cursor-pointer group">
                    <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition-transform">
                      <UploadCloud className="w-8 h-8" />
                    </div>
                    <p className="text-on-surface font-bold text-lg mb-1">Drag and drop an image, or click to browse</p>
                    <p className="text-secondary text-sm">Supports JPG, PNG, WEBP, and AVIF for advanced metadata forensics.</p>
                  </div>
                )}

                {activeTab === 'url' && (
                  <div className="flex items-center gap-3 bg-surface-container-low border border-outline-variant/15 rounded-xl p-4 transition-all focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary">
                    <LinkIcon className="w-6 h-6 text-secondary" />
                    <input 
                      type="url"
                      className="bg-transparent border-none text-lg focus:ring-0 p-0 w-full placeholder:text-secondary/50 outline-none text-on-surface" 
                      placeholder="https://example.com/suspicious-article" 
                    />
                  </div>
                )}
              </div>
              {/* Action Bar */}
              <div className="flex items-center justify-between pt-4">
                <div className="flex gap-4">
                  <button type="button" onClick={() => alert('Language auto-detected: English')} className="flex items-center gap-2 text-sm font-medium text-secondary hover:text-primary transition-colors">
                    <Sparkles className="w-4 h-4" />
                    Auto-detect Language
                  </button>
                  <button type="button" onClick={() => alert('Context Tuning options open')} className="flex items-center gap-2 text-sm font-medium text-secondary hover:text-primary transition-colors">
                    <Network className="w-4 h-4" />
                    Context Tuning
                  </button>
                </div>
                <button 
                  type="button"
                  onClick={() => setShowAnalysis(true)} 
                  className="bg-gradient-to-br from-primary to-primary-container text-white px-8 py-4 rounded-xl font-bold text-lg shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center gap-3">
                  <span>Analyze Content</span>
                  <BarChart3 className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

        </div>

        {/* Right Content: Analysis Report */}
        {showAnalysis && (
          <div className="lg:col-span-7 xl:col-span-8">
            <AnalysisReport />
          </div>
        )}
      </main>
      <footer className="bg-surface border-t border-outline-variant/5 py-12">
        <div className="max-w-4xl mx-auto px-6 flex justify-end items-center">
          <div className="text-sm text-secondary font-medium">
            © 2026 Bit2Byte
          </div>
        </div>
      </footer>
    </div>
  );
}
