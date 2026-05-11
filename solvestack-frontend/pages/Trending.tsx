
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Problem } from '../types';
import { apiService } from '../services/api';
import ProblemCard from '../components/ProblemCard';
import {
    TrendingUp,
    LayoutGrid,
    Sparkles,
    Terminal,
    Loader2,
    ChevronLeft
} from 'lucide-react';

const Trending: React.FC = () => {
    const [problems, setProblems] = useState<Problem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTrending = async () => {
            setLoading(true);
            const data = await apiService.getTrendingProblems();
            setProblems(data);
            setLoading(false);
        };
        fetchTrending();
    }, []);

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
                    <Link to="/dashboard" className="flex items-center gap-3 px-4 py-3 rounded-xl text-white/40 hover:text-white hover:bg-white/5 transition-all">
                        <LayoutGrid className="w-5 h-5" />
                        Problem Shelf
                    </Link>
                    <Link to="/trending" className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/10 text-white font-medium transition-all">
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
                {/* Header */}
                <header className="p-6 border-b border-white/5 bg-black/40 backdrop-blur-xl sticky top-0 z-20">
                    <div className="max-w-[1600px] mx-auto flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Link to="/dashboard" className="p-2 hover:bg-white/5 rounded-xl transition-colors text-white/40 hover:text-white">
                                <ChevronLeft className="w-5 h-5" />
                            </Link>
                            <div>
                                <h1 className="text-2xl font-bold flex items-center gap-3">
                                    <TrendingUp className="w-6 h-6 text-cyan-400" />
                                    Trending Problems
                                </h1>
                                <p className="text-sm text-white/40">The most liked technical challenges this week</p>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Scrollable Area */}
                <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
                    {loading ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                            {[1, 2, 3, 4, 5, 6].map(i => (
                                <div key={i} className="h-[300px] bg-[#090909] border border-white/5 animate-pulse rounded-2xl relative overflow-hidden">
                                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full animate-[shimmer_2s_infinite]" />
                                </div>
                            ))}
                        </div>
                    ) : (
                        <>
                            {problems.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                                    {problems.map(problem => (
                                        <ProblemCard key={problem.id} problem={problem} />
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-20 bg-[#090909] border border-white/5 border-dashed rounded-3xl">
                                    <TrendingUp className="w-16 h-16 text-white/10 mx-auto mb-4" />
                                    <h3 className="text-xl font-bold mb-2">No trending problems yet</h3>
                                    <p className="text-white/40 max-sm mx-auto">Check back later once the community has engaged more!</p>
                                </div>
                            )}
                        </>
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

// Internal Components or missing icons
const Layers = ({ className }: { className?: string }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2" /><polyline points="2 17 12 22 22 17" /><polyline points="2 12 12 17 22 12" /></svg>
);

export default Trending;
