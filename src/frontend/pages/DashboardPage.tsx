import React from 'react';
import AnalysisResultContent from '../components/dashboard/AnalysisResultContent';

const DashboardPage = React.memo(() => {
  return (
    <div className="lg:ml-64 pt-20 pb-12 px-6 md:px-10 lg:px-12">
      <div className="max-w-7xl mx-auto">
        <AnalysisResultContent />
      </div>
    </div>
  );
});

DashboardPage.displayName = 'DashboardPage';

export default DashboardPage;
