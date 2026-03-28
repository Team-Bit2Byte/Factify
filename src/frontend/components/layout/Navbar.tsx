import React, { useEffect, useState, useCallback } from 'react';
import { Search, Moon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { APP_CONFIG } from '../../constants/config';

export const Navbar = React.memo(() => {
  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem("theme") === "dark"
  );

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  const toggleTheme = useCallback(() => setDarkMode(prev => !prev), []);

  return (
    <header className="fixed top-0 w-full z-50 bg-slate-50/80 backdrop-blur-xl shadow-sm flex justify-between items-center px-6 py-3">
      <div className="flex items-center gap-4">
        <Link to="/" className="text-xl font-black tracking-tighter text-primary">
          {APP_CONFIG.name}
        </Link>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center bg-surface-container-low px-4 py-1.5 rounded-full border border-outline-variant/15">
          <Search className="text-secondary w-4 h-4 mr-2" />
          <input 
            className="bg-transparent border-none text-sm focus:ring-0 p-0 w-32 placeholder:text-slate-400 text-black" 
            placeholder="Search hash..." 
            type="text"
            aria-label="Search by hash"
          />
        </div>
        <button
          onClick={toggleTheme}
          className="p-2 text-slate-500 hover:bg-slate-200/50 rounded-full transition-colors"
          aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
        >
          <Moon className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
});
