import React from 'react';
import { LayoutDashboard, SearchCheck, Settings, Plus, HelpCircle } from 'lucide-react';
import { cn } from '@/src/lib/utils';
import { useLocation, Link } from 'react-router-dom';

export function Sidebar() {
  const location = useLocation();

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: SearchCheck, label: 'Analysis History', path: '#' },
    { icon: Settings, label: 'Settings', path: '#' },
  ];

  return (
    <aside className="hidden lg:flex flex-col h-screen w-64 fixed left-0 top-0 pt-20 bg-slate-100 p-4 gap-2">
      <div className="mb-8 px-2">
        <h2 className="text-lg font-bold text-slate-900">Forensic AI</h2>
        <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Veracity Engine v1.0</p>
      </div>
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => (
          item.path === '#' ? (
            <button
              key={item.label}
              onClick={(e) => { e.preventDefault(); alert(`${item.label} coming soon!`); }}
              className={cn(
                "flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all text-slate-600 hover:bg-slate-200"
              )}
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
            >
              <item.icon className="w-5 h-5" />
              <span className="text-sm font-medium">{item.label}</span>
            </Link>
          )
        ))}
      </nav>
      <div className="mt-auto pt-4 border-t border-slate-200">
        <button 
          onClick={() => alert('New Analysis flow coming soon!')}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-br from-primary to-primary-container text-white py-3 rounded-xl font-bold text-sm shadow-lg shadow-primary/20 hover:scale-[0.98] transition-transform"
        >
          <Plus className="w-4 h-4" />
          New Analysis
        </button>
        <button 
          onClick={(e) => { e.preventDefault(); alert('Help Center coming soon!'); }}
          className="w-full flex items-center gap-3 px-4 py-2.5 mt-4 text-slate-600 hover:bg-slate-200 transition-all rounded-lg"
        >
          <HelpCircle className="w-5 h-5" />
          <span className="text-sm font-medium">Help Center</span>
        </button>
      </div>
    </aside>
  );
}
