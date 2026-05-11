
import React from 'react';
import { Problem, Difficulty } from '../types';
import { PLATFORM_ICONS, DIFFICULTY_COLORS } from '../constants';
import { Heart, Users, ExternalLink, ArrowUpRight, Sparkles, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import InferenceOverlay from './InferenceOverlay';

interface ProblemCardProps {
  problem: Problem;
}

const ProblemCard: React.FC<ProblemCardProps> = ({ problem }) => {
  const { isAuthenticated, refreshUser } = useAuth();
  // Note: ProblemCard is used in Dashboard which is under AuthProvider (App.tsx)

  // We need local state to track interest if the backend doesn't return "isInterested" for the user yet
  const [interested, setInterested] = React.useState(problem.isInterested || false);
  const [count, setCount] = React.useState(problem.interestedCount);
  const [loadingInterest, setLoadingInterest] = React.useState(false);

  // Expo Showmanship States
  const [isOverlayOpen, setIsOverlayOpen] = React.useState(false);
  const [overlayLoading, setOverlayLoading] = React.useState(false);
  const [explanationData, setExplanationData] = React.useState<any>(null);
  const [prototypeData, setPrototypeData] = React.useState<any>(null);

  // Sync state if problem prop changes
  React.useEffect(() => {
    setInterested(problem.isInterested || false);
    setCount(problem.interestedCount);
  }, [problem.isInterested, problem.interestedCount]);

  const handleToggleInterest = async (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent Link navigation
    e.stopPropagation();

    if (!isAuthenticated) {
      // Redirect to login or show alert
      if (confirm("You need to be logged in to track interests. Go to login?")) {
        window.location.href = '#/login';
      }
      return;
    }

    if (loadingInterest) return;
    setLoadingInterest(true);

    try {
      if (interested) {
        const newCount = await apiService.removeInterest(problem.id);
        if (newCount !== null) {
          setInterested(false);
          setCount(newCount);
          refreshUser();
        }
      } else {
        const newCount = await apiService.toggleInterest(problem.id);
        if (newCount !== null) {
          setInterested(true);
          setCount(newCount);
          refreshUser();
        }
      }
    } catch (error) {
      console.error("Failed to toggle interest", error);
    } finally {
      setLoadingInterest(false);
    }
  };

  const handleShowIntelligence = async (mode: 'explain' | 'prototype') => {
    setIsOverlayOpen(true);
    if (mode === 'explain' && explanationData) return;
    if (mode === 'prototype' && prototypeData) return;

    setOverlayLoading(true);
    try {
      const [expl, proto] = await Promise.all([
        explanationData ? Promise.resolve(explanationData) : apiService.getExplanation(problem.id),
        mode === 'prototype' ? apiService.getPrototype(problem.id) : Promise.resolve(prototypeData)
      ]);
      setExplanationData(expl);
      if (proto) setPrototypeData(proto);
    } catch (error) {
      console.error("Failed to fetch intelligence", error);
    } finally {
      setOverlayLoading(false);
    }
  };

  // Use the canonical difficulty from the backend to match the Dashboard filter
  const displayDifficulty = problem.difficulty;

  return (
    <div className="group relative bg-[#090909] border border-white/5 rounded-xl p-5 hover:border-white/20 transition-all duration-300 hover:shadow-[0_0_20px_rgba(255,255,255,0.05)]">
      <div className="flex justify-between items-start mb-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <div className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border w-fit ${DIFFICULTY_COLORS[displayDifficulty]}`}>
              {displayDifficulty}
            </div>
            {problem.isNew && (
              <div className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-green-500/20 text-green-400 border border-green-500/30 animate-pulse">
                NEW
              </div>
            )}
          </div>
          {problem.engineeringImpactScore !== undefined && (
            <button
              onClick={() => handleShowIntelligence('explain')}
              className="flex items-center gap-1.5 px-2 py-0.5 bg-cyan-500/10 hover:bg-cyan-500/20 rounded border border-cyan-500/30 w-fit transition-colors group/eis"
            >
              <Sparkles className="w-3 h-3 text-cyan-400 group-hover/eis:scale-110 transition-transform" />
              <span className="text-[10px] font-bold text-cyan-50/80">EIS: {problem.engineeringImpactScore.toFixed(0)}</span>
              <span className="text-[9px] text-cyan-400/0 group-hover/eis:text-cyan-400/100 ml-1 transition-all">Why?</span>
            </button>
          )}
        </div>
        <div className="flex items-center gap-2 opacity-60 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => handleShowIntelligence('explain')}
            className="flex items-center gap-1.5 px-2 py-1 bg-white/5 hover:bg-cyan-500/10 border border-white/5 hover:border-cyan-500/30 rounded-lg transition-all"
            title="Show Intelligence Breakdown"
          >
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span className="text-[10px] font-bold text-white/40 group-hover:text-cyan-400">Why this rank?</span>
          </button>
          {PLATFORM_ICONS[problem.source]}
          <span className="text-[11px] font-medium">{problem.source}</span>
        </div>
      </div>

      <Link to={`/problem/${problem.id}`} className="block group/title">
        <h3 className="text-lg font-semibold text-white/90 group-hover/title:text-white transition-colors mb-2 line-clamp-2 flex items-center gap-1">
          {problem.title}
          <ArrowUpRight className="w-4 h-4 opacity-0 group-hover/title:opacity-100 -translate-x-1 group-hover/title:translate-x-0 transition-all" />
        </h3>
      </Link>

      <p className="text-sm text-white/50 mb-4 line-clamp-3 leading-relaxed">
        {problem.description}
      </p>

      <div className="flex flex-wrap gap-1.5 mb-6">
        {problem.techStack.slice(0, 4).map((tech) => (
          <span key={tech} className="px-2 py-0.5 bg-white/5 rounded-full text-[11px] font-medium text-white/70">
            {tech}
          </span>
        ))}
        {problem.techStack.length > 4 && (
          <span className="text-[11px] text-white/30 flex items-center">+{problem.techStack.length - 4}</span>
        )}
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-white/5">
        <div className="flex items-center gap-4">
          <button
            onClick={handleToggleInterest}
            className={`flex items-center gap-1.5 transition-colors text-xs font-medium ${interested ? 'text-red-500 hover:text-red-400' : 'text-white/40 hover:text-red-400'}`}
          >
            <Heart className={`w-4 h-4 ${interested ? 'fill-current' : ''}`} />
            {count}
          </button>
          {/* Hiding Launch Prototype for now due to Quota issues */}
          {/* 
          <button
            onClick={() => handleShowIntelligence('prototype')}
            className="flex items-center gap-1.5 text-cyan-500/60 hover:text-cyan-400 transition-colors text-xs font-bold"
          >
            <Zap className="w-4 h-4" />
            Launch Prototype
          </button>
          */}
        </div>
        <a
          href={problem.sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 text-white/40 hover:text-white hover:bg-white/5 rounded-lg transition-all"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>

      {/* Hiding Primary Launch Prototype button for now */}
      {/* 
      <button
        onClick={() => handleShowIntelligence('prototype')}
        className="w-full mt-4 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-black uppercase tracking-widest rounded-xl transition-all shadow-lg active:scale-95 flex items-center justify-center gap-2"
      >
        <Zap className="w-3.5 h-3.5 fill-current" />
        Launch Prototype
      </button>
      */}

      <InferenceOverlay
        isOpen={isOverlayOpen}
        onClose={() => setIsOverlayOpen(false)}
        problemTitle={problem.title}
        explanationData={explanationData}
        prototypeData={prototypeData}
        loading={overlayLoading}
      />
    </div>
  );
};

export default ProblemCard;
