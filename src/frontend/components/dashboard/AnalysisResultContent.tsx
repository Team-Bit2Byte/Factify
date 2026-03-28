import React from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  Globe,
  HelpCircle,
  Image as ImageIcon,
  ScanText,
  ShieldAlert,
} from 'lucide-react';
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

function formatVerdict(verdict?: AnalysisResult['detection']['verdict']) {
  switch (verdict) {
    case 'likely_original':
      return {
        label: 'Likely Original',
        badgeClass: 'bg-emerald-100 text-emerald-700',
        ringClass: 'text-emerald-500',
        panelClass: 'from-emerald-50 to-white',
        icon: CheckCircle2,
      };
    case 'unverified':
      return {
        label: 'Unverified',
        badgeClass: 'bg-amber-100 text-amber-700',
        ringClass: 'text-amber-500',
        panelClass: 'from-amber-50 to-white',
        icon: HelpCircle,
      };
    default:
      return {
        label: 'Likely Fake / False',
        badgeClass: 'bg-rose-100 text-rose-700',
        ringClass: 'text-rose-500',
        panelClass: 'from-rose-50 to-white',
        icon: ShieldAlert,
      };
  }
}

const AnalysisResultContent = React.memo<AnalysisResultContentProps>(({ className = '', analysisData }) => {
  if (!analysisData) {
    return (
      <div className={className}>
        <div className="rounded-3xl border border-dashed border-outline-variant/30 bg-white/70 p-8 text-center shadow-sm">
          <ClipboardCheck className="mx-auto mb-4 h-10 w-10 text-primary" />
          <h2 className="text-2xl font-black tracking-tight text-on-surface">Run an analysis to see the verdict</h2>
          <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-secondary">
            Factify will classify the content as Likely Original, Unverified, or Likely Fake / False and show the extracted evidence here.
          </p>
        </div>
      </div>
    );
  }

  const extractedText = normalizeField(analysisData.combined_text);
  const headline = normalizeField(analysisData.headline) || 'Untitled analysis';
  const body = normalizeField(analysisData.body) || extractedText;
  const source = normalizeField(analysisData.source);
  const caption = normalizeField(analysisData.caption);
  const resolvedUrl = normalizeField(analysisData.url);
  const methodLabel = normalizeField(analysisData.engine_used);
  const dates = uniqueItems(analysisData.dates ?? []);
  const people = uniqueItems(analysisData.people ?? []);
  const organizations = uniqueItems(analysisData.organizations ?? []);
  const locations = uniqueItems(analysisData.locations ?? []);
  const suspiciousElements = uniqueItems(analysisData.suspicious_elements ?? []);
  const detection = analysisData.detection;
  const algorithms = analysisData.algorithms;
  const verdictUi = formatVerdict(detection?.verdict);
  const VerdictIcon = verdictUi.icon;
  const fakeProbability = detection?.fake_probability ?? 0;
  const originalProbability = detection?.original_probability ?? 0;
  const confidence = detection?.confidence ?? 'low';
  const confidenceScore = detection?.confidence_score ?? 0;
  const findings = detection?.findings?.length ? detection.findings : suspiciousElements;
  const inputType = analysisData.input_type ?? 'image';
  const algorithmOverall = algorithms?.overall_score ?? 0;
  const moduleScores = algorithms?.module_scores ?? {};
  const topModules = Object.entries(moduleScores).sort((a, b) => b[1] - a[1]).slice(0, 4);
  const tweetModel = analysisData.tweet_model;
  const showTweetModel = inputType === 'text' && tweetModel?.enabled;

  return (
    <div className={className}>
      <section className="mb-8 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-3">
          <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] ${verdictUi.badgeClass}`}>
            <VerdictIcon className="h-4 w-4" />
            {detection?.verdict_label || verdictUi.label}
          </span>
          <div>
            <h1 className="max-w-3xl text-2xl font-black leading-tight tracking-tight text-on-surface sm:text-3xl lg:text-4xl">
              {headline}
            </h1>
            <p className="mt-2 text-sm text-secondary">
              Input: <span className="font-semibold text-on-surface capitalize">{inputType}</span>
              {' • '}
              Engine: <span className="font-semibold text-on-surface">{methodLabel || 'model inference'}</span>
              {' • '}
              Runtime: <span className="font-semibold text-on-surface">{analysisData.processing_time_sec.toFixed(2)}s</span>
            </p>
          </div>
        </div>

        <div className="rounded-2xl border border-outline-variant/15 bg-white px-4 py-3 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-secondary">Confidence</p>
          <p className="mt-1 text-2xl font-black text-on-surface">{confidenceScore}%</p>
          <p className="text-sm capitalize text-secondary">{confidence}</p>
        </div>
      </section>

      <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-12">
        <section className={`overflow-hidden rounded-3xl border border-outline-variant/10 bg-gradient-to-br ${verdictUi.panelClass} p-6 shadow-sm lg:col-span-5`}>
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-secondary">Model verdict</p>
              <h2 className="mt-2 text-2xl font-black text-on-surface">{detection?.verdict_label || verdictUi.label}</h2>
            </div>
            <VerdictIcon className={`h-10 w-10 ${verdictUi.ringClass}`} />
          </div>

          <div className="relative mx-auto mb-6 flex h-44 w-44 items-center justify-center">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
              <circle className="text-surface-container" cx="50" cy="50" fill="transparent" r="44" stroke="currentColor" strokeWidth="8" />
              <circle
                className={`${verdictUi.ringClass} transition-all duration-700`}
                cx="50"
                cy="50"
                fill="transparent"
                r="44"
                stroke="currentColor"
                strokeDasharray="276"
                strokeDashoffset={276 - (276 * fakeProbability) / 100}
                strokeLinecap="round"
                strokeWidth="8"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-5xl font-black leading-none text-on-surface">{fakeProbability}%</span>
              <span className="mt-1 text-xs font-bold uppercase tracking-[0.18em] text-secondary">Fake risk</span>
            </div>
          </div>

          <p className="text-sm leading-6 text-secondary">
            {detection?.summary || 'The model did not provide a textual summary.'}
          </p>
        </section>

        <section className="rounded-3xl border border-outline-variant/10 bg-surface-container-low p-6 shadow-sm lg:col-span-7">
          <div className="mb-6 flex items-center gap-2">
            <ClipboardCheck className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-bold text-on-surface">Evidence snapshot</h2>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-secondary">Likely original</p>
              <p className="mt-2 text-3xl font-black text-on-surface">{originalProbability}%</p>
              <p className="mt-1 text-sm text-secondary">Signal supporting legitimate reporting patterns.</p>
            </div>

            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-secondary">Likely fake / false</p>
              <p className="mt-2 text-3xl font-black text-on-surface">{fakeProbability}%</p>
              <p className="mt-1 text-sm text-secondary">Signal matching misinformation-like language patterns.</p>
            </div>
          </div>

          <div className="mt-4 rounded-2xl bg-white p-4 shadow-sm">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-secondary">Algorithm engine score</p>
            <p className="mt-2 text-3xl font-black text-on-surface">{algorithmOverall}</p>
            <p className="mt-1 text-sm text-secondary">
              Deterministic credibility score blended into the final verdict.
            </p>
          </div>

          <div className="mt-6 rounded-2xl bg-white p-5 shadow-sm">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-secondary">Key findings</p>
            <div className="mt-4 space-y-3">
              {findings.length ? (
                findings.map((finding, index) => (
                  <div key={`${finding}-${index}`} className="flex items-start gap-3">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <p className="text-sm leading-6 text-on-surface">{finding}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-secondary">No additional findings were returned for this analysis.</p>
              )}
            </div>
          </div>
        </section>
      </div>

      <div className="mb-8 grid grid-cols-1 gap-6 xl:grid-cols-3">
        <section className="rounded-2xl border border-outline-variant/10 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <FileText className="h-5 w-5 text-primary" />
            <h3 className="text-lg font-bold text-on-surface">Content</h3>
          </div>
          <div className="space-y-2 text-sm text-secondary">
            <p><span className="font-semibold text-on-surface">Words:</span> {body.split(/\s+/).filter(Boolean).length}</p>
            <p><span className="font-semibold text-on-surface">Source:</span> {source || 'Not detected'}</p>
            <p><span className="font-semibold text-on-surface">Suspicious flags:</span> {suspiciousElements.length}</p>
            <p><span className="font-semibold text-on-surface">Source trust band:</span> {algorithms?.source_label || 'unknown'}</p>
          </div>
        </section>

        <section className="rounded-2xl border border-outline-variant/10 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            {inputType === 'url' ? <Globe className="h-5 w-5 text-primary" /> : <ImageIcon className="h-5 w-5 text-primary" />}
            <h3 className="text-lg font-bold text-on-surface">Input details</h3>
          </div>
          <div className="space-y-2 text-sm text-secondary">
            <p><span className="font-semibold text-on-surface">Type:</span> {inputType}</p>
            {resolvedUrl ? <p><span className="font-semibold text-on-surface">URL:</span> {resolvedUrl}</p> : null}
            {caption ? <p><span className="font-semibold text-on-surface">Caption:</span> {caption}</p> : null}
            {analysisData.ocr_region_count ? <p><span className="font-semibold text-on-surface">OCR regions:</span> {analysisData.ocr_region_count}</p> : null}
          </div>
        </section>

        <section className="rounded-2xl border border-outline-variant/10 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <ScanText className="h-5 w-5 text-primary" />
            <h3 className="text-lg font-bold text-on-surface">Entities</h3>
          </div>
          <div className="space-y-3 text-sm text-secondary">
            <p><span className="font-semibold text-on-surface">People:</span> {people.join(', ') || 'None'}</p>
            <p><span className="font-semibold text-on-surface">Organizations:</span> {organizations.join(', ') || 'None'}</p>
            <p><span className="font-semibold text-on-surface">Locations:</span> {locations.join(', ') || 'None'}</p>
            <p><span className="font-semibold text-on-surface">Dates:</span> {dates.join(', ') || 'None'}</p>
          </div>
        </section>
      </div>

      <section className="mb-8 grid grid-cols-1 gap-6 xl:grid-cols-2">
        <article className="rounded-3xl border border-outline-variant/10 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-on-surface">Extracted text</h2>
          <p className="mt-2 text-sm leading-7 text-secondary whitespace-pre-wrap">
            {body || extractedText || 'No text content was extracted.'}
          </p>
        </article>

        <article className="rounded-3xl border border-outline-variant/10 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-on-surface">Model metadata</h2>
          <div className="mt-4 space-y-3 text-sm text-secondary">
            <p><span className="font-semibold text-on-surface">Raw score:</span> {detection?.raw_score ?? 0}</p>
            <p><span className="font-semibold text-on-surface">Confidence band:</span> {confidence}</p>
            <p><span className="font-semibold text-on-surface">Primary label:</span> {detection?.verdict_label || verdictUi.label}</p>
            {showTweetModel ? <p><span className="font-semibold text-on-surface">Tweet text model:</span> {tweetModel?.verdict_label}</p> : null}
          </div>
        </article>
      </section>

      {showTweetModel ? (
        <section className="mb-8 grid grid-cols-1 gap-6 xl:grid-cols-2">
          <article className="rounded-3xl border border-outline-variant/10 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold text-on-surface">Tweet text model</h2>
            <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="rounded-2xl bg-surface-container-low p-4">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-secondary">Verdict</p>
                <p className="mt-2 text-lg font-black text-on-surface">{tweetModel?.verdict_label}</p>
              </div>
              <div className="rounded-2xl bg-surface-container-low p-4">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-secondary">Fake risk</p>
                <p className="mt-2 text-3xl font-black text-on-surface">{tweetModel?.fake_probability}%</p>
              </div>
              <div className="rounded-2xl bg-surface-container-low p-4">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-secondary">Coverage</p>
                <p className="mt-2 text-3xl font-black text-on-surface">{tweetModel?.coverage_ratio}%</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-secondary">
              {tweetModel?.summary}
            </p>
          </article>

          <article className="rounded-3xl border border-outline-variant/10 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold text-on-surface">Tweet model notes</h2>
            <div className="mt-4 space-y-3 text-sm text-secondary">
              <p><span className="font-semibold text-on-surface">Model:</span> {tweetModel?.model_name}</p>
              <p><span className="font-semibold text-on-surface">Threshold:</span> {tweetModel?.threshold_used}</p>
              <p><span className="font-semibold text-on-surface">Derived features:</span> {tweetModel?.derived_feature_count} / {tweetModel?.feature_count}</p>
              <p><span className="font-semibold text-on-surface">Confidence band:</span> {tweetModel?.confidence}</p>
              {(tweetModel?.notes || []).map((note) => (
                <p key={note}>{note}</p>
              ))}
            </div>
          </article>
        </section>
      ) : null}

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <article className="rounded-3xl border border-outline-variant/10 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-on-surface">Algorithm module scores</h2>
          <div className="mt-4 space-y-4">
            {topModules.length ? topModules.map(([name, score]) => (
              <div key={name}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="font-semibold capitalize text-on-surface">{name.replace(/_/g, ' ')}</span>
                  <span className="text-secondary">{score}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-surface-container">
                  <div className="h-full bg-primary" style={{ width: `${score}%` }} />
                </div>
              </div>
            )) : (
              <p className="text-sm text-secondary">No algorithm score breakdown is available.</p>
            )}
          </div>
        </article>

        <article className="rounded-3xl border border-outline-variant/10 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-on-surface">Algorithm evidence</h2>
          <div className="mt-4 space-y-3 text-sm text-secondary">
            <p><span className="font-semibold text-on-surface">Suspicious phrases:</span> {algorithms?.suspicious_phrases?.join(', ') || 'None'}</p>
            <p><span className="font-semibold text-on-surface">Claim flags:</span> {algorithms?.claim_flags?.join(', ') || 'None'}</p>
            <p><span className="font-semibold text-on-surface">Top negative terms:</span> {algorithms?.top_negative_terms?.map((item) => item.term).join(', ') || 'None'}</p>
            <p><span className="font-semibold text-on-surface">Greedy signals:</span> {algorithms?.greedy_signals?.map((item) => item.pattern_name).join(', ') || 'None'}</p>
          </div>
          <div className="mt-5 space-y-2">
            {(algorithms?.explanations || []).slice(0, 4).map((line) => (
              <p key={line} className="text-sm leading-6 text-secondary">{line}</p>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
});

AnalysisResultContent.displayName = 'AnalysisResultContent';

export default AnalysisResultContent;
