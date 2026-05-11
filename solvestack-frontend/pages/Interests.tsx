
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Problem } from '../types';
import { apiService } from '../services/api';
import ProblemCard from '../components/ProblemCard';
import {
    Heart,
    Search,
    LayoutGrid,
    TrendingUp,
    Layers,
    Users,
    Clock,
    ArrowLeft,
    Loader2
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const Interests: React.FC = () => {
    const { user, isAuthenticated } = useAuth();
    const [problems, setProblems] = useState<Problem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchInterests = async () => {
            if (!isAuthenticated) return;
            try {
                const data = await apiService.getUserInterests();
                setProblems(data);
            } catch (error) {
                console.error("Failed to fetch interests:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchInterests();
    }, [isAuthenticated]);

    if (!isAuthenticated) {
        return (
            <div className="min-h-screen bg-black flex flex-col items-center justify-center p-6 text-center">
                <Heart className="w-16 h-16 text-white/10 mb-6" />
                <h2 className="text-2xl font-bold text-white mb-2">Authentication Required</h2>
                <p className="text-white/40 mb-8 max-w-sm">
                    Please sign in to view and manage your interested problems.
                </p>
                <Link
                    to="/login"
                    className="px-8 py-3 bg-white text-black font-bold rounded-xl hover:bg-white/90 transition-all"
                >
                    Sign In
                </Link>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen bg-black text-white">
            {/* Sidebar - Minimal version for now or we could reuse a component if it existed */}
            <aside className="w-64 border-r border-white/5 p-6 hidden md:flex flex-col">
                <Link to="/dashboard" className="flex items-center gap-2 mb-10 group">
                    <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                    <span className="text-sm font-bold">Back to Dashboard</span>
                </Link>

                <nav className="space-y-1 flex-1">
                    <Link to="/dashboard" className="flex items-center gap-3 px-4 py-3 text-white/40 hover:text-white transition-colors rounded-xl">
                        <LayoutGrid className="w-5 h-5" />
                        <span className="text-sm font-bold">All Problems</span>
                    </Link>
                    <div className="flex items-center gap-3 px-4 py-3 bg-white/5 text-white rounded-xl">
                        <Heart className="w-5 h-5 fill-current text-red-500" />
                        <span className="text-sm font-bold">My Interests</span>
                    </div>
                    <Link to="/squads" className="flex items-center gap-3 px-4 py-3 text-white/40 hover:text-white transition-colors rounded-xl">
                        <Users className="w-5 h-5" />
                        <span className="text-sm font-bold">Your Squads</span>
                    </Link>
                    <Link to="/profile" className="flex items-center gap-3 px-4 py-3 text-white/40 hover:text-white transition-colors rounded-xl">
                        <Layers className="w-5 h-5" />
                        <span className="text-sm font-bold">My Solutions</span>
                    </Link>
                </nav>
            </aside>

            <main className="flex-1 flex flex-col h-screen overflow-hidden">
                <header className="p-8 border-b border-white/5 flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-black mb-1">My Interests</h1>
                        <p className="text-sm text-white/40">Problems you've marked as interesting to solve.</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-xs font-bold">
                            {problems.length} Problems
                        </div>
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto p-8">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-64 text-white/20">
                            <Loader2 className="w-8 h-8 animate-spin mb-4" />
                            <span className="text-sm font-medium">Loading your interests...</span>
                        </div>
                    ) : problems.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                            {problems.map((problem) => (
                                <ProblemCard key={problem.id} problem={problem} />
                            ))}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-64 text-center">
                            <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mb-6">
                                <Heart className="w-10 h-10 text-white/10" />
                            </div>
                            <h3 className="text-xl font-bold mb-2">No Interests Yet</h3>
                            <p className="text-white/40 mb-8 max-w-xs">
                                Browse problems on the dashboard and click the heart icon to save them here.
                            </p>
                            <Link
                                to="/dashboard"
                                className="px-6 py-2 border border-white/10 rounded-xl text-sm font-bold hover:bg-white/5 transition-all"
                            >
                                Explore Problems
                            </Link>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default Interests;
