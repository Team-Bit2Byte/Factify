import React from 'react';
import { AlertTriangle, Share, Download, ClipboardCheck, XCircle, FileText, Image, ShieldCheck } from 'lucide-react';
import { MOCK_ANALYSIS_DATA } from '../../constants/config';
import type { AnalysisResult } from '../../services/api';

interface AnalysisResultContentProps {
  className?: string;
  analysisData?: AnalysisResult | null;
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
  const resolvedUrl = normalizeField(analysisData?.url);
  const isUrlAnalysis = analysisData?.input_type === 'url' || Boolean(resolvedUrl);
  const methodLabel = normalizeField(analysisData?.engine_used) || (isUrlAnalysis ? 'scraper' : 'ocr');
  const people = uniqueItems(analysisData?.people ?? []);
  const organizations = uniqueItems(analysisData?.organizations ?? []);
  const locations = uniqueItems(analysisData?.locations ?? []);
  const dates = uniqueItems(analysisData?.dates ?? []);
  const suspiciousElements = uniqueItems(analysisData?.suspicious_elements ?? []);
  const hasRealAnalysis = Boolean(analysisData && (extractedText || body || headline));

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
      <section className="mb-10 flex flex-col gap-6 md:mb-12 md:flex-row md:items-start md:justify-between md:gap-8">
        <div className="space-y-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-error-container text-error text-[10px] font-bold uppercase tracking-widest">
            <AlertTriangle className="w-3 h-3 fill-current" />
            Likely Fake
          </span>
          <h1 className="max-w-2xl text-2xl font-black leading-tight tracking-tight text-on-surface sm:text-3xl lg:text-5xl">
            {data.title}
          </h1>
          <p className="flex flex-wrap items-center gap-2 text-sm font-medium text-secondary">
            Analysed on {data.analysisDate} • <span className="text-on-surface">Article ID: {data.articleId}</span>
          </p>
        </div>
        <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row sm:shrink-0">
          <button 
            onClick={() => alert('Share dialog coming soon!')}
            className="flex items-center justify-center gap-2 rounded-lg bg-surface-container-highest px-4 py-2 text-sm font-bold text-on-surface transition-colors hover:bg-surface-variant"
            aria-label="Share analysis"
          >
            <Share className="w-4 h-4" />
            Share
          </button>
          <button 
            onClick={() => alert('PDF export started!')}
            className="flex items-center justify-center gap-2 rounded-lg bg-surface-container-highest px-4 py-2 text-sm font-bold text-on-surface transition-colors hover:bg-surface-variant"
            aria-label="Export as PDF"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </section>

      {/* Top Bento Grid: Score & Summary */}
      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Score Display (4/12) */}
        <div className="relative overflow-hidden rounded-3xl border border-outline-variant/10 bg-white p-6 text-center shadow-sm group sm:p-8 lg:col-span-4">
          <div className="absolute top-0 right-0 p-4">
            <span className="flex items-center gap-1 text-tertiary font-bold text-xs bg-tertiary-fixed-dim/30 px-2 py-1 rounded-full">
              Confidence: {data.confidence.charAt(0).toUpperCase() + data.confidence.slice(1)}
            </span>
          </div>
          <div className="relative mx-auto mb-6 flex h-36 w-36 items-center justify-center sm:h-44 sm:w-44 lg:h-48 lg:w-48">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle className="text-surface-container" cx="50" cy="50" fill="transparent" r="44" stroke="currentColor" strokeWidth="8"></circle>
              <circle className="text-error transition-all duration-1000" cx="50" cy="50" fill="transparent" r="44" stroke="currentColor" strokeDasharray="276" strokeDashoffset="50" strokeLinecap="round" strokeWidth="8"></circle>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-black leading-none text-on-surface sm:text-5xl">{data.probability}%</span>
              <span className="text-xs uppercase tracking-widest text-secondary mt-1 font-bold">Probability</span>
            </div>
          </div>
          <h3 className="text-xl font-bold text-on-surface mb-2">Fake News Detected</h3>
          <p className="text-sm text-secondary leading-relaxed">Highly correlated with known misinformation patterns in geopolitical reporting.</p>
        </div>

        {/* Explanation Panel (8/12) */}
        <div className="flex flex-col rounded-3xl bg-surface-container-low p-6 sm:p-8 lg:col-span-8">
          <div className="flex items-center gap-2 mb-6">
            <ClipboardCheck className="text-primary w-6 h-6" />
            <h2 className="text-xl font-bold">Veracity Verdict</h2>
          </div>
          <div className="grid h-full grid-cols-1 gap-6 xl:grid-cols-2 xl:gap-8">
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
      <div className="mb-12 grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
        {/* Text Analysis Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-outline-variant/10 group hover:border-primary/20 transition-all">
          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
            <FileText className="text-primary w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold mb-2">Text Analysis</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-4 py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Sentiment</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-error-container text-error rounded">{data.textAnalysis.sentiment}</span>
            </div>
            <div className="flex items-center justify-between gap-4 py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Clickbait Score</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-error-container text-error rounded">{data.textAnalysis.clickbaitScore} / 10</span>
            </div>
            <div className="flex items-center justify-between gap-4 py-2">
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
            <div className="flex items-center justify-between gap-4 py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Manipulation</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-error-container text-error rounded">
                {data.imageForensics.manipulation.charAt(0).toUpperCase() + data.imageForensics.manipulation.slice(1)}
              </span>
            </div>
            <div className="flex items-center justify-between gap-4 py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">ELA Result</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">{data.imageForensics.elaResult}</span>
            </div>
            <div className="flex items-center justify-between gap-4 py-2">
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
            <div className="flex items-center justify-between gap-4 py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Blacklist Status</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-error-container text-error rounded">
                {data.domainTrust.blacklistStatus.charAt(0).toUpperCase() + data.domainTrust.blacklistStatus.slice(1)}
              </span>
            </div>
            <div className="flex items-center justify-between gap-4 py-2 border-b border-outline-variant/10">
              <span className="text-sm text-secondary">Domain Age</span>
              <span className="text-xs font-bold px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded">{data.domainTrust.domainAge}</span>
            </div>
            <div className="flex items-center justify-between gap-4 py-2">
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
              <h2 className="text-2xl font-black tracking-tight sm:text-3xl">Extracted Text</h2>
              <p className="text-secondary text-sm">
                {isUrlAnalysis
                  ? 'Article text scraped from the provided URL is shown below.'
                  : 'OCR output from the uploaded image is shown below.'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <article className="rounded-3xl border border-outline-variant/10 bg-white p-5 shadow-sm sm:p-6 xl:col-span-2">
              <div className="flex flex-wrap items-center gap-3 mb-4 text-xs font-bold uppercase tracking-[0.2em] text-secondary">
                <span>{methodLabel}</span>
                {!isUrlAnalysis && <span>{analysisData?.ocr_region_count ?? 0} regions</span>}
                {isUrlAnalysis && resolvedUrl && <span>web article</span>}
                <span>{analysisData?.processing_time_sec?.toFixed(2) ?? '0.00'}s</span>
              </div>

              {headline && (
                <div className="mb-5">
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-secondary mb-2">Headline</p>
                  <h3 className="text-xl font-bold leading-tight text-on-surface sm:text-2xl">{headline}</h3>
                </div>
              )}

              {body && (
                <div className="mb-5">
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-secondary mb-2">Body</p>
                  <p className="whitespace-pre-wrap text-sm leading-7 text-on-surface md:text-base">{body}</p>
                </div>
              )}

              <div>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-secondary mb-2">
                  {isUrlAnalysis ? 'Full Extracted Text' : 'Full OCR Text'}
                </p>
                <div className="max-h-80 overflow-y-auto rounded-2xl border border-outline-variant/10 bg-surface-container-low p-4 sm:p-5">
                  <p className="whitespace-pre-wrap break-words text-sm leading-7 text-on-surface md:text-base">
                    {extractedText}
                  </p>
                </div>
              </div>
            </article>

            <div className="space-y-6">
              <article className="rounded-3xl border border-outline-variant/10 bg-surface-container-low p-5 sm:p-6">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-secondary mb-4">
                  {isUrlAnalysis ? 'Source Metadata' : 'Image Metadata'}
                </p>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between gap-4">
                    <span className="text-secondary">{isUrlAnalysis ? 'Method' : 'Image Type'}</span>
                    <span className="break-words text-right font-semibold text-on-surface">
                      {isUrlAnalysis ? methodLabel : (analysisData?.image_type || 'unknown')}
                    </span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-secondary">Source</span>
                    <span className="font-semibold text-on-surface text-right">{source || 'Not identified'}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-secondary">{isUrlAnalysis ? 'URL' : 'Caption'}</span>
                    <span className="font-semibold text-on-surface text-right break-all">
                      {isUrlAnalysis ? (resolvedUrl || 'Not available') : (caption || 'Not generated')}
                    </span>
                  </div>
                </div>
              </article>

              <article className="rounded-3xl border border-outline-variant/10 bg-white p-5 shadow-sm sm:p-6">
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

              <article className="rounded-3xl bg-on-surface p-5 text-white sm:p-6">
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
    </div>
  );
});

AnalysisResultContent.displayName = 'AnalysisResultContent';

export default AnalysisResultContent;
