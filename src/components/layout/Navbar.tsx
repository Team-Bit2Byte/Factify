import React from 'react';
import { Search, Moon, History, User } from 'lucide-react';
import { Link } from 'react-router-dom';

export function Navbar() {
  return (
    <header className="fixed top-0 w-full z-50 bg-slate-50/80 backdrop-blur-xl shadow-sm flex justify-between items-center px-6 py-3">
      <div className="flex items-center gap-4">
        <Link to="/" className="text-xl font-black tracking-tighter text-primary">
          Forensic Editorial
        </Link>
        <nav className="hidden md:flex items-center gap-6 ml-8">
          <Link to="/dashboard" className="text-primary font-bold tracking-tight">Dashboard</Link>
          <a className="text-slate-500 hover:bg-slate-200/50 transition-colors px-3 py-1 rounded-lg" href="#">Reports</a>
          <a className="text-slate-500 hover:bg-slate-200/50 transition-colors px-3 py-1 rounded-lg" href="#">Sources</a>
        </nav>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center bg-surface-container-low px-4 py-1.5 rounded-full border border-outline-variant/15">
          <Search className="text-secondary w-4 h-4 mr-2" />
          <input 
            className="bg-transparent border-none text-sm focus:ring-0 p-0 w-32 placeholder:text-slate-400" 
            placeholder="Search hash..." 
            type="text"
          />
        </div>
        <button className="p-2 text-slate-500 hover:bg-slate-200/50 rounded-full transition-colors">
          <Moon className="w-5 h-5" />
        </button>
        <button className="p-2 text-slate-500 hover:bg-slate-200/50 rounded-full transition-colors">
          <History className="w-5 h-5" />
        </button>
        <div className="w-8 h-8 rounded-full border border-outline-variant/20 overflow-hidden">
          <img 
            alt="User Profile" 
            src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
          />
        </div>
      </div>
    </header>
  );
}
