import React, { useMemo, useCallback } from 'react';
import { LayoutDashboard, SearchCheck, Settings, Plus, HelpCircle } from 'lucide-react';
import { useLocation, Link } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { APP_CONFIG } from '../../constants/config';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: SearchCheck, label: 'Analysis History', path: '#' },
  { icon: Settings, label: 'Settings', path: '#' },
] as const;

export const Sidebar = React.memo(() => {
  const location = useLocation();

  const handlePlaceholderClick = useCallback((label: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    alert(`${label} coming soon!`);
  }, []);

  const handleNewAnalysis = useCallback(() => {
    alert('New Analysis flow coming soon!');
  }, []);

  const handleHelpCenter = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    alert('Help Center coming soon!');
  }, []);

  const navElements = useMemo(() => (
    navItems.map((item) => (
      item.path === '#' ? (
        <button
          key={item.label}
          onClick={handlePlaceholderClick(item.label)}
          className={cn(
            "flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all text-slate-600 hover:bg-slate-200"
          )}
          aria-label={item.label}
        >
          <item.icon className="w-5 h-5" />
          <span className="text-sm font-medium">{item.label}</span>
        </button>
      ) : (
        <Link
          key={item.label}
          to={item.path}
          className={cn(
            "flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all",
            location.pathname === item.path
              ? "bg-white text-primary font-bold shadow-sm translate-x-1"
              : "text-slate-600 hover:bg-slate-200"
          )}
          aria-label={item.label}
          aria-current={location.pathname === item.path ? 'page' : undefined}
        >
          <item.icon className="w-5 h-5" />
          <span className="text-sm font-medium">{item.label}</span>
        </Link>
      )
    ))
  ), [location.pathname, handlePlaceholderClick]);

  return (
    <aside className="hidden lg:flex flex-col h-screen w-64 fixed left-0 top-0 pt-20 bg-slate-100 p-4 gap-2">
      <div className="mb-8 px-2">
        <h2 className="text-lg font-bold text-slate-900">{APP_CONFIG.tagline}</h2>
        <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Veracity Engine v1.0</p>
      </div>
      <nav className="flex flex-col gap-1" aria-label="Main navigation">
        {navElements}
      </nav>
      <div className="mt-auto pt-4 border-t border-slate-200">
        <button 
          onClick={handleNewAnalysis}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-br from-primary to-primary-container text-white py-3 rounded-xl font-bold text-sm shadow-lg shadow-primary/20 hover:scale-[0.98] transition-transform"
          aria-label="Start new analysis"
        >
          <Plus className="w-4 h-4" />
          New Analysis
        </button>
        <button 
          onClick={handleHelpCenter}
          className="w-full flex items-center gap-3 px-4 py-2.5 mt-4 text-slate-600 hover:bg-slate-200 transition-all rounded-lg"
          aria-label="Open help center"
        >
          <HelpCircle className="w-5 h-5" />
          <span className="text-sm font-medium">Help Center</span>
        </button>
      </div>
    </aside>
  );
});
