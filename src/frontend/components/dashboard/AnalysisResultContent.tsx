import React from 'react';
import { AlertTriangle, Share, Download, ClipboardCheck, XCircle, FileText, Image, ShieldCheck, ArrowRight, Brain, Verified, ArrowLeftRight, Shield } from 'lucide-react';
import { MOCK_ANALYSIS_DATA } from '../../constants/config';
import type { ImageAnalysisResult } from '../../services/api';

interface AnalysisResultContentProps {
  className?: string;
  analysisData?: ImageAnalysisResult | null;
}

function normalizeField(value?: string | null) {
  if (!value) {
    return '';
  }

  const trimmed = value.trim();
  return trimmed && trimmed !== 'None' ? trimmed : '';
}

function uniqueItems(items: string[]) {
  return [...new Set(items.filter(Boolean))];
}

const AnalysisResultContent = React.memo<AnalysisResultContentProps>(({ className = '', analysisData }) => {
  // If we have real data from image analysis, format it. Otherwise use mock data.
  const extractedText = normalizeField(analysisData?.combined_text);
  const headline = normalizeField(analysisData?.headline);
  const body = normalizeField(analysisData?.body);
  const source = normalizeField(analysisData?.source);
  const caption = normalizeField(analysisData?.caption);
  const people = uniqueItems(analysisData?.people ?? []);
  const organizations = uniqueItems(analysisData?.organizations ?? []);
  const locations = uniqueItems(analysisData?.locations ?? []);
  const dates = uniqueItems(analysisData?.dates ?? []);
  const suspiciousElements = uniqueItems(analysisData?.suspicious_elements ?? []);
  const hasRealAnalysis = Boolean(analysisData && extractedText);

  const data = analysisData ? {
    ...MOCK_ANALYSIS_DATA,
    title: headline || extractedText.slice(0, 100) || MOCK_ANALYSIS_DATA.title,
    content: body || extractedText,
    extractedText,
    // Add entities data from analysis
    entities: {
      people,
      organizations,
      locations,
      dates,
    },
    suspiciousElements,
  } : MOCK_ANALYSIS_DATA;

  return (
    <div className={className}>
      {/* Header Section */}
      <section className="flex flex-col md:flex-row justify-between items-start gap-8 mb-12">
        <div className="space-y-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-error-container text-error text-[10px] font-bold uppercase tracking-widest">
            <AlertTriangle className="w-3 h-3 fill-current" />
            Likely Fake
          </span>
          <h1 className="text-3xl lg:text-5xl font-black tracking-tight text-on-surface leading-tight max-w-2xl">
            {data.title}
          </h1>
          <p className="text-secondary font-medium flex items-center gap-2 text-sm">
            Analysed on {data.analysisDate} • <span className="text-on-surface">Article ID: {data.articleId}</span>
          </p>
        </div>
        <div className="flex gap-3 shrink-0">
          <button 
            onClick={() => alert('Share dialog coming soon!')}
            className="flex items-center gap-2 px-4 py-2 bg-surface-container-highest text-on-surface rounded-lg font-bold text-sm hover:bg-surface-variant transition-colors"
            aria-label="Share analysis"
          >
            <Share className="w-4 h-4" />
            Share
          </button>
          <button 
            onClick={() => alert('PDF export started!')}
            className="flex items-center gap-2 px-4 py-2 bg-surface-container-highest text-on-surface rounded-lg font-bold text-sm hover:bg-surface-variant transition-colors"
            aria-label="Export as PDF"
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
              Confidence: {data.confidence.charAt(0).toUpperCase() + data.confidence.slice(1)}
            </span>
          </div>
          <div className="relative w-48 h-48 mb-6 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle className="text-surface-container" cx="50" cy="50" fill="transparent" r="44" stroke="currentColor" strokeWidth="8"></circle>
              <circle className="text-error transition-all duration-1000" cx="50" cy="50" fill="transparent" r="44" stroke="currentColor" strokeDasharray="276" strokeDashoffset="50" strokeLinecap="round" strokeWidth="8"></circle>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-5xl font-black text-on-surface leading-none">{data.probability}%</span>
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
                {data.findings.map((finding, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <XCircle className="text-error w-5 h-5 fill-current shrink-0" />
                    <p className="text-sm font-medium">{finding.message}</p>
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-white/50 rounded-2xl p-6 border border-white/80">
              <h4 className="text-sm font-bold uppercase tracking-wider text-secondary mb-4">Neural Map Breakdown</h4>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs font-bold mb-1.5">
                    <span>Syntax Deviation</span>
                    <span>{data.metrics.syntaxDeviation}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-error" style={{ width: `${data.metrics.syntaxDeviation}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-bold mb-1.5">
                    <span>Semantic Consistency</span>
                    <span>{data.metrics.semanticConsistency}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-error" style={{ width: `${data.metrics.semanticConsistency}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-bold mb-1.5">
                    <span>Authority Alignment</span>
                    <span>{data.metrics.authorityAlignment}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                    <div className="h-full bg-error" style={{ width: `${data.metrics.authorityAlignment}%` }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Detail Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {/* Text Analysis Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-outline-variant/10 group hover:border-primary/20 transition-all">
          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <FileText className="text-primary w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold mb-2">Text Analysis</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Sentiment</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-error-container text-error rounded">{data.textAnalysis.sentiment}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Clickbait Score</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-error-container text-error rounded">{data.textAnalysis.clickbaitScore} / 10</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-secondary">AI Authored</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">
                {data.textAnalysis.aiAuthored.isLikely ? 'Likely' : 'Unlikely'} ({data.textAnalysis.aiAuthored.probability}%)
              </span>
            </div>
          </div>
        </div>

        {/* Image Analysis Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-outline-variant/10 group hover:border-primary/20 transition-all">
          <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <Image className="text-secondary w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold mb-2">Image Forensics</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Manipulation</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-error-container text-error rounded">
                {data.imageForensics.manipulation.charAt(0).toUpperCase() + data.imageForensics.manipulation.slice(1)}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">ELA Result</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">{data.imageForensics.elaResult}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-secondary">Origin</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">{data.imageForensics.origin}</span>
            </div>
          </div>
        </div>

        {/* Source Credibility Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-outline-variant/10 group hover:border-primary/20 transition-all">
          <div className="w-12 h-12 rounded-xl bg-tertiary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <ShieldCheck className="text-tertiary w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold mb-2">Domain Trust</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Blacklist Status</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-error-container text-error rounded">
                {data.domainTrust.blacklistStatus.charAt(0).toUpperCase() + data.domainTrust.blacklistStatus.slice(1)}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Domain Age</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">{data.domainTrust.domainAge}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-secondary">IP Location</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">{data.domainTrust.ipLocation}</span>
            </div>
          </div>
        </div>
      </div>

      {hasRealAnalysis && (
        <section className="mb-12 space-y-6">
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-primary" />
            <div>
              <h2 className="text-3xl font-black tracking-tight">Extracted Text</h2>
              <p className="text-secondary text-sm">
                OCR output from the uploaded image is shown below.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <article className="xl:col-span-2 bg-white rounded-3xl border border-outline-variant/10 shadow-sm p-6">
              <div className="flex flex-wrap items-center gap-3 mb-4 text-xs font-bold uppercase tracking-[0.2em] text-secondary">
                <span>{analysisData?.engine_used || 'OCR'}</span>
                <span>{analysisData?.ocr_region_count ?? 0} regions</span>
                <span>{analysisData?.processing_time_sec?.toFixed(2) ?? '0.00'}s</span>
              </div>

              {headline && (
                <div className="mb-5">
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-secondary mb-2">Headline</p>
                  <h3 className="text-2xl font-bold text-on-surface leading-tight">{headline}</h3>
                </div>
              )}

              {body && (
                <div className="mb-5">
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-secondary mb-2">Body</p>
                  <p className="text-sm md:text-base leading-7 text-on-surface whitespace-pre-wrap">{body}</p>
                </div>
              )}

              <div>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-secondary mb-2">Full OCR Text</p>
                <div className="max-h-80 overflow-y-auto rounded-2xl bg-surface-container-low p-5 border border-outline-variant/10">
                  <p className="text-sm md:text-base leading-7 text-on-surface whitespace-pre-wrap">
                    {extractedText}
                  </p>
                </div>
              </div>
            </article>

            <div className="space-y-6">
              <article className="bg-surface-container-low rounded-3xl border border-outline-variant/10 p-6">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-secondary mb-4">Image Metadata</p>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between gap-4">
                    <span className="text-secondary">Image Type</span>
                    <span className="font-semibold text-on-surface">{analysisData?.image_type || 'unknown'}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-secondary">Source</span>
                    <span className="font-semibold text-on-surface text-right">{source || 'Not identified'}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-secondary">Caption</span>
                    <span className="font-semibold text-on-surface text-right">{caption || 'Not generated'}</span>
                  </div>
                </div>
              </article>

              <article className="bg-white rounded-3xl border border-outline-variant/10 shadow-sm p-6">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-secondary mb-4">Detected Entities</p>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm font-semibold text-on-surface mb-2">People</p>
                    <p className="text-sm text-secondary">{people.join(', ') || 'None detected'}</p>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-on-surface mb-2">Organizations</p>
                    <p className="text-sm text-secondary">{organizations.join(', ') || 'None detected'}</p>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-on-surface mb-2">Locations</p>
                    <p className="text-sm text-secondary">{locations.join(', ') || 'None detected'}</p>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-on-surface mb-2">Dates</p>
                    <p className="text-sm text-secondary">{dates.join(', ') || 'None detected'}</p>
                  </div>
                </div>
              </article>

              <article className="bg-on-surface rounded-3xl p-6 text-white">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-white/50 mb-3">Suspicious Elements</p>
                <div className="space-y-3">
                  {(suspiciousElements.length ? suspiciousElements : ['No suspicious elements detected']).map((item) => (
                    <div key={item} className="rounded-2xl bg-white/8 px-4 py-3 text-sm leading-6">
                      {item}
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </div>
        </section>
      )}

      {/* Detailed Visual Evidence */}
      <section>
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-3xl font-black tracking-tight">Visual Forensics</h2>
          <button 
            onClick={() => alert('Full metadata panel coming soon!')}
            className="text-primary font-bold text-sm flex items-center gap-1 hover:underline"
          >
            View Full Metadata <ArrowRight className="w-3 h-3" />
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="relative rounded-3xl overflow-hidden aspect-video shadow-2xl">
            <img 
              alt="Digital manipulation analysis showing compression artifacts" 
              className="w-full h-full object-cover"
              src="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=1000"
              referrerPolicy="no-referrer"
              loading="lazy"
              width="1000"
              height="563"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-8">
              <div>
                <h4 className="text-white font-bold text-xl">Compression Anomaly Detected</h4>
                <p className="text-white/80 text-sm">Zone 4: Artificial pixel interpolation suggests generative filling.</p>
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-6">
            <div className="glass-panel p-6 rounded-3xl border border-white/40 flex-1">
              <h4 className="font-bold text-lg mb-4">Neural Comparison</h4>
              <div className="flex gap-4">
                <div className="flex-1 text-center">
                  <div className="bg-surface-container h-32 rounded-xl mb-2 flex items-center justify-center">
                    <Brain className="text-error w-8 h-8" />
                  </div>
                  <span className="text-xs font-bold uppercase text-secondary">Target Sample</span>
                </div>
                <div className="flex items-center">
                  <ArrowLeftRight className="text-secondary w-6 h-6" />
                </div>
                <div className="flex-1 text-center">
                  <div className="bg-surface-container h-32 rounded-xl mb-2 flex items-center justify-center">
                    <Verified className="text-primary w-8 h-8" />
                  </div>
                  <span className="text-xs font-bold uppercase text-secondary">Verified Baseline</span>
                </div>
              </div>
              <p className="text-sm text-secondary mt-4 italic">"Structural patterns diverge significantly from journalistic standards for this topic."</p>
            </div>
            <div className="bg-on-surface rounded-3xl p-6 text-white flex items-center justify-between">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-white/50 mb-1">Global Verdict Integrity</p>
                <p className="text-2xl font-black">99.8%</p>
              </div>
              <Shield className="w-10 h-10 text-primary-container fill-current" />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
});

AnalysisResultContent.displayName = 'AnalysisResultContent';

export default AnalysisResultContent;
