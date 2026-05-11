
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Problem, Difficulty, Source } from '../types';
import { apiService } from '../services/api';
import ProblemCard from '../components/ProblemCard';
import {
  Search,
  Filter,
  TrendingUp,
  Layers,
  Clock,
  Sparkles,
  LayoutGrid,
  X,
  Loader2,
  Code2,
  Globe,
  Terminal,
  MessageSquare,
  RefreshCcw
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { GoogleGenAI, Type } from "@google/genai";

const Dashboard: React.FC = () => {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const LIMIT = 40;
  const [hasMore, setHasMore] = useState(true);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('All');
  const [selectedPlatform, setSelectedPlatform] = useState<string>('All');

  // AI Filtering States
  const [aiFilteredIds, setAiFilteredIds] = useState<string[] | null>(null);
  const [isAiFiltering, setIsAiFiltering] = useState(false);

  // Scraping State
  const [isScraping, setIsScraping] = useState(false);

  // Auto-search: debounce searchQuery changes
  useEffect(() => {
    if (!searchQuery.trim()) {
      // Cleared — reset to normal browse mode
      if (aiFilteredIds !== null) {
        setAiFilteredIds(null);
        setLoading(true);
        apiService.getProblems(0, LIMIT).then(data => {
          setProblems(data);
          setOffset(LIMIT);
          setHasMore(data.length === LIMIT);
          setLoading(false);
        });
      }
      return;
    }
    const timer = setTimeout(() => handleAiFilter(), 400);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      const data = await apiService.getProblems(0, LIMIT);
      setProblems(data);
      setOffset(LIMIT);
      setHasMore(data.length === LIMIT);

      if (data.length === 0) {
        // Shelf is empty, auto-trigger the scrapers
        setIsScraping(true);
        try {
          const result = await apiService.scrapeProblems();
          if (result.newProblems && result.newProblems.length > 0) {
            const newProblemsWithBadge = result.newProblems.map(p => ({ ...p, isNew: true }));
            setProblems(newProblemsWithBadge);
            setHasMore(newProblemsWithBadge.length >= LIMIT);
          }
        } catch (error) {
          console.error("Auto-scraping failed:", error);
        } finally {
          setIsScraping(false);
        }
      }

      setLoading(false);
    };
    fetch();
  }, []);

  const handleLoadMore = async () => {
    setLoadingMore(true);
    const data = await apiService.getProblems(offset, LIMIT);
    if (data.length < LIMIT) {
      setHasMore(false);
    }
    setProblems(prev => [...prev, ...data]);
    setOffset(prev => prev + LIMIT);
    setLoadingMore(false);
  };

  const handleAiFilter = async () => {
    if (!searchQuery.trim()) return;

    setIsAiFiltering(true);
    try {
      // Try semantic search first, then fall back to keyword search
      let results = await apiService.semanticSearch(searchQuery);
      if (!results || results.length === 0) {
        results = await apiService.keywordSearch(searchQuery);
      }
      setProblems(results);
      setAiFilteredIds([]); // Marker for being in search mode
      setHasMore(false);
    } catch (error) {
      console.error("AI Filtering failed, trying keyword fallback", error);
      try {
        const results = await apiService.keywordSearch(searchQuery);
        setProblems(results);
        setAiFilteredIds([]);
        setHasMore(false);
      } catch (e2) {
        console.error("Keyword search also failed", e2);
        setAiFilteredIds(null);
      }
    } finally {
      setIsAiFiltering(false);
    }
  };

  const clearAiFilter = async () => {
    setAiFilteredIds(null);
    setSearchQuery('');
    setLoading(true);
    const data = await apiService.getProblems(0, LIMIT);
    setProblems(data);
    setOffset(LIMIT);
    setHasMore(data.length === LIMIT);
    setLoading(false);
  };

  const handleRunScrapers = async () => {
    setIsScraping(true);
    try {
      const result = await apiService.scrapeProblems();

      if (result.newProblems && result.newProblems.length > 0) {
        // Prepend new problems smoothly and mark them as new
        const newProblemsWithBadge = result.newProblems.map(p => ({ ...p, isNew: true }));
        setProblems(prev => [...newProblemsWithBadge, ...prev]);

        // Optional: show a small toast or notification if we had a library for it
        console.log(`Added ${result.newProblems.length} new problems to the shelf.`);
      } else {
        console.log("No new problems found in this sync.");
      }
    } catch (error) {
      console.error("Scraping failed:", error);
      alert("Scraping failed. Please check the backend logs.");
    } finally {
      setIsScraping(false);
    }
  };

  const filteredProblems = problems.filter(p => {
    // Difficulty filter always applies
    const matchesDifficulty = selectedDifficulty === 'All' || p.difficulty === selectedDifficulty;
    // Platform filter always applies
    const matchesPlatform = selectedPlatform === 'All' || 
      (selectedPlatform === 'GitHub' && p.source === Source.GITHUB) ||
      (selectedPlatform === 'Hacker News' && p.source === Source.HACKERNEWS) ||
      (selectedPlatform === 'Stack Overflow' && p.source === Source.STACKOVERFLOW);

    // If AI filter returned results, show them (already filtered by server)
    // but still apply difficulty and platform filters
    if (aiFilteredIds !== null) {
      const matchesAi = aiFilteredIds.length === 0 ? true : aiFilteredIds.includes(p.id);
      return matchesAi && matchesDifficulty && matchesPlatform;
    }

    // Local text search filter
    const q = searchQuery.toLowerCase();
    const matchesSearch = !q || 
      p.title.toLowerCase().includes(q) ||
      (p.description || '').toLowerCase().includes(q) ||
      (p.humanExplanation || '').toLowerCase().includes(q) ||
      p.techStack.some(t => t.toLowerCase().includes(q));
    return matchesSearch && matchesDifficulty && matchesPlatform;
  });

  const chartData = [
    { name: 'Stack Overflow', count: problems.filter(p => p.source === Source.STACKOVERFLOW).length },
    { name: 'GitHub', count: problems.filter(p => p.source === Source.GITHUB).length },
    { name: 'Hacker News', count: problems.filter(p => p.source === Source.HACKERNEWS).length }
  ];

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-black text-white">
      {/* Sidebar - Desktop */}
      <aside className="w-full md:w-64 border-r border-white/5 p-6 flex flex-col gap-8">
        <Link to="/" className="flex items-center gap-2 mb-4 group">
          <div className="w-8 h-8 bg-white rounded-md flex items-center justify-center group-hover:scale-105 transition-transform">
            <span className="text-black font-bold">S</span>
          </div>
          <span className="text-xl font-bold hover:text-white/80 transition-colors">SolveStack</span>
        </Link>

        <nav className="flex flex-col gap-2">
          <Link to="/dashboard" className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/10 text-white font-medium transition-all">
            <LayoutGrid className="w-5 h-5" />
            Problem Shelf
          </Link>
          <Link to="/trending" className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/40 hover:text-white hover:bg-white/5 transition-all">
            <TrendingUp className="w-5 h-5" />
            Trending
          </Link>
          <Link to="/squads" className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/40 hover:text-white hover:bg-white/5 transition-all">
            <Layers className="w-5 h-5" />
            Your Squads
          </Link>
          <Link to="/interests" className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/40 hover:text-white hover:bg-white/5 transition-all">
            <Sparkles className="w-5 h-5" />
            Interests
          </Link>
          <Link to="/profile" className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/40 hover:text-white hover:bg-white/5 transition-all">
            <Terminal className="w-5 h-5" />
            Profile
          </Link>
        </nav>

        {/* <div className="mt-auto p-4 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-500/10 border border-white/5">
          <h4 className="text-sm font-bold mb-1">Pro Feature</h4>
          <p className="text-xs text-white/50 mb-3">Get real-time alerts for problems in your stack.</p>
          <button className="w-full py-2 bg-white text-black text-xs font-bold rounded-lg hover:bg-white/90 transition-all">
            Upgrade Now
          </button>
        </div> */}
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-[#050505]">
        {/* Header / Toolbar Area */}
        <header className="p-6 border-b border-white/5 bg-black/40 backdrop-blur-xl sticky top-0 z-20">
          <div className="max-w-[1600px] mx-auto flex flex-col xl:flex-row xl:items-center justify-between gap-6">

            {/* Search Section */}
            <div className="relative flex-1 max-w-2xl group">
              <div className="absolute inset-x-0 -bottom-px h-px bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent opacity-0 group-focus-within:opacity-100 transition-opacity" />
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-cyan-400 transition-colors" />
                <input
                  type="text"
                  placeholder="Describe a problem or technology..."
                  className="w-full bg-white/[0.03] border border-white/10 rounded-2xl py-3.5 pl-12 pr-12 text-sm focus:outline-none focus:bg-white/[0.07] focus:border-cyan-500/30 transition-all placeholder:text-white/20 text-white"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAiFilter()}
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                  {aiFilteredIds && (
                    <button
                      onClick={clearAiFilter}
                      className="p-1.5 hover:bg-white/10 rounded-full transition-colors text-white/40 hover:text-white"
                      title="Clear AI Filter"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={handleAiFilter}
                    disabled={isAiFiltering}
                    className={`p-2 rounded-xl transition-all ${isAiFiltering ? 'bg-cyan-500/20 text-cyan-500' : 'bg-white/5 text-white/40 hover:text-cyan-400 hover:bg-cyan-500/10 border border-white/5'}`}
                    title="AI Semantic Filter"
                  >
                    {isAiFiltering ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Filter Section */}
            <div className="flex flex-wrap items-center gap-4">
              {/* Platform Filter */}
              <div className="flex items-center p-1 bg-white/[0.03] border border-white/10 rounded-2xl">
                {['All', 'GitHub', 'Hacker News', 'Stack Overflow'].map((platform) => {
                  const Icon = platform === 'GitHub' ? Terminal :
                    platform === 'Hacker News' ? Globe :
                      platform === 'Stack Overflow' ? Code2 :
                        platform === 'Reddit' ? MessageSquare : LayoutGrid;
                  return (
                    <button
                      key={platform}
                      onClick={() => {
                        setSelectedPlatform(platform);
                        setAiFilteredIds(null);
                      }}
                      className={`px-3 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${selectedPlatform === platform ? 'bg-cyan-500 text-black shadow-lg shadow-cyan-500/20' : 'text-white/40 hover:text-white hover:bg-white/5'}`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span className={platform === 'All' ? 'inline' : 'hidden xl:inline'}>{platform}</span>
                    </button>
                  );
                })}
              </div>

              {/* Difficulty Filter */}
              <div className="flex items-center p-1 bg-white/[0.03] border border-white/10 rounded-2xl">
                {['All', Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.ADVANCED].map((diff) => (
                  <button
                    key={diff}
                    onClick={() => {
                      setSelectedDifficulty(diff);
                      setAiFilteredIds(null);
                    }}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${selectedDifficulty === diff ? 'bg-white text-black' : 'text-white/40 hover:text-white hover:bg-white/5'}`}
                  >
                    {diff}
                  </button>
                ))}
              </div>

              {/* Run Scrapers Button */}
              <button
                onClick={handleRunScrapers}
                disabled={isScraping}
                className={`flex items-center gap-2 px-4 py-2 rounded-2xl text-xs font-bold transition-all border ${isScraping ? 'bg-white/5 text-white/20 border-white/5' : 'bg-white/5 text-white/60 hover:text-white hover:bg-white/10 border-white/10'}`}
                title="Run background scrapers to fetch new problems"
              >
                {isScraping ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
                {isScraping ? 'Scraping...' : 'Sync Problems'}
              </button>
            </div>
          </div>
        </header>

        {/* Scrollable Area */}
        <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
          {aiFilteredIds !== null && (
            <div className="mb-6 flex items-center gap-3">
              <div className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full flex items-center gap-2">
                <Sparkles className="w-3 h-3 text-cyan-400" />
                <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">AI Context Filter Active</span>
              </div>
              <button
                onClick={clearAiFilter}
                className="text-xs text-white/30 hover:text-white transition-colors underline underline-offset-4"
              >
                Clear Results
              </button>
            </div>
          )}

          {/* Analytics Snapshot Removed */}

          {/* Problems Feed */}

          {/* Problems Feed */}
          {loading || isAiFiltering ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="h-[300px] bg-[#090909] border border-white/5 animate-pulse rounded-2xl relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full animate-[shimmer_2s_infinite]" />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredProblems.map(problem => (
                <ProblemCard key={problem.id} problem={problem} />
              ))}
            </div>
          )}

          {!loading && !isAiFiltering && filteredProblems.length === 0 && (
            <div className="text-center py-20 bg-[#090909] border border-white/5 border-dashed rounded-3xl">
              <div className="text-white/10 mb-4 flex justify-center">
                <Search className="w-16 h-16" />
              </div>
              <h3 className="text-xl font-bold mb-2">No matching problems on the shelf</h3>
              <p className="text-white/40 max-sm mx-auto">Try broadening your search or use the semantic filter for better results.</p>
              <button
                onClick={clearAiFilter}
                className="mt-6 px-6 py-2 bg-white/5 border border-white/10 rounded-full text-xs font-bold hover:bg-white/10 transition-all"
              >
                Reset Filter
              </button>
            </div>
          )}

          {/* Load More Button */}
          {!loading && hasMore && !isAiFiltering && filteredProblems.length > 0 && (
            <div className="mt-8 flex justify-center">
              <button
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="px-8 py-3 bg-white text-black font-bold rounded-full hover:bg-white/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
              >
                {loadingMore && <Loader2 className="w-4 h-4 animate-spin" />}
                {loadingMore ? 'Loading...' : 'Load More Problems'}
              </button>
            </div>
          )}
        </div>
      </main>

      <style>{`
        @keyframes shimmer {
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
