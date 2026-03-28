import React from 'react';
import AnalysisResultContent from './AnalysisResultContent';
import type { AnalysisResult } from '../../services/api';

interface AnalysisReportProps {
  analysisData?: AnalysisResult | null;
}

const AnalysisReport = React.memo<AnalysisReportProps>(({ analysisData }) => {
  return (
    <div className="w-full h-full bg-surface-container-lowest/50 backdrop-blur-xl rounded-3xl p-6 md:p-8 shadow-sm border border-outline-variant/15 animate-in fade-in slide-in-from-right-8 duration-700">
      <AnalysisResultContent analysisData={analysisData} />
    </div>
  );
});

AnalysisReport.displayName = 'AnalysisReport';

export default AnalysisReport;
