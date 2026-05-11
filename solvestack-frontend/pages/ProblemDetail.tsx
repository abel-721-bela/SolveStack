
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Problem, SolutionType } from '../types';
import { apiService } from '../services/api';
import {
  ArrowLeft,
  ExternalLink,
  MessageSquare,
  Users,
  Heart,
  Cpu,
  Code,
  Layers,
  Sparkles,
  Zap,
  Loader2,
  BarChart3,
  Plus,
  Check,
  Send,
  X
} from 'lucide-react';
import { GoogleGenAI, Type } from "@google/genai";
import { useAuth } from '../contexts/AuthContext';
import InferenceOverlay from '../components/InferenceOverlay';

// Helper for clock since Lucide clock was used but not imported in detail
const Clock: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
);

const ProblemDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated, refreshUser } = useAuth();
  const [problem, setProblem] = useState<Problem | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiInsight, setAiInsight] = useState<string>('');
  const [loadingAi, setLoadingAi] = useState(false);

  const [interested, setInterested] = useState(false);
  const [count, setCount] = useState(0);
  const [loadingInterest, setLoadingInterest] = useState(false);

  // Expo Showmanship States
  const [isOverlayOpen, setIsOverlayOpen] = useState(false);
  const [overlayLoading, setOverlayLoading] = useState(false);
  const [explanationData, setExplanationData] = useState<any>(null);
  const [prototypeData, setPrototypeData] = useState<any>(null);

  // Squad System States
  const [squads, setSquads] = useState<any[]>([]);
  const [loadingSquads, setLoadingSquads] = useState(false);
  const [showCreateSquad, setShowCreateSquad] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', description: '' });
  const [creatingSquad, setCreatingSquad] = useState(false);
  const [joiningId, setJoiningId] = useState<number | null>(null);

  useEffect(() => {
    const fetch = async () => {
      if (!id) return;
      const data = await apiService.getProblemById(id);
      if (data) {
        setProblem(data);
        setInterested(data.isInterested || false);
        setCount(data.interestedCount || 0);
      }
      setLoading(false);
    };
    fetch();
  }, [id]);

  const fetchProblemSquads = React.useCallback(async () => {
    if (!id) return;
    setLoadingSquads(true);
    try {
      const data = await apiService.getSquads();
      const numId = parseInt(id);
      const filtered = data.filter((sq: any) => sq.problem_id === numId);
      filtered.sort((a: any, b: any) => b.member_count - a.member_count);

      const token = localStorage.getItem('token');
      if (token && isAuthenticated) {
        const enriched = await Promise.all(filtered.map(async (sq: any) => {
          try {
            const detail = await apiService.getSquadDetail(sq.id);
            return {
              ...sq,
              user_request_status: detail.user_request_status,
              pending_requests: detail.pending_requests?.length ?? sq.pending_requests,
              is_leader: detail.is_leader,
              is_member: detail.is_member
            };
          } catch { return sq; }
        }));
        setSquads(enriched);
      } else {
        setSquads(filtered);
      }
    } catch (error) {
      console.error("Failed to fetch squads", error);
    } finally {
      setLoadingSquads(false);
    }
  }, [id, isAuthenticated]);

  useEffect(() => {
    fetchProblemSquads();
  }, [fetchProblemSquads]);

  const handleToggleInterest = async () => {
    if (!isAuthenticated) {
      alert("Please sign in to favorite problems");
      return;
    }
    if (!problem || loadingInterest) return;

    setLoadingInterest(true);
    try {
      if (interested) {
        const success = await apiService.removeInterest(problem.id);
        if (success) {
          setInterested(false);
          setCount(prev => prev - 1);
          refreshUser();
        }
      } else {
        const success = await apiService.toggleInterest(problem.id);
        if (success) {
          setInterested(true);
          setCount(prev => prev + 1);
          refreshUser();
        }
      }
    } catch (error) {
      console.error("Failed to toggle interest", error);
    } finally {
      setLoadingInterest(false);
    }
  };

  const handleJoinSquad = async (squadId: number) => {
    if (!isAuthenticated) { alert("Please sign in to join squads"); return; }
    setJoiningId(squadId);
    try {
      await apiService.joinSquad(squadId);
      await fetchProblemSquads();
    } catch (e: any) {
      alert(e.message || 'Failed to send join request');
    } finally {
      setJoiningId(null);
    }
  };

  const handleCreateSquad = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!problem || !createForm.name.trim()) return;
    setCreatingSquad(true);
    try {
      await apiService.createSquad(problem.id, createForm.name.trim(), createForm.description.trim());
      await fetchProblemSquads();
      setShowCreateSquad(false);
      setCreateForm({ name: '', description: '' });
    } catch (e: any) {
      alert(e.message || 'Failed to create squad');
    } finally {
      setCreatingSquad(false);
    }
  };

  const handleDeleteSquad = async (squadId: number) => {
    if (!window.confirm("Are you sure you want to permanently delete this squad? This action cannot be undone.")) return;
    try {
      await apiService.deleteSquad(squadId);
      await fetchProblemSquads();
    } catch (e: any) {
      alert(e.message || 'Failed to delete squad');
    }
  };

  const handleLeaveSquad = async (squadId: number) => {
    if (!window.confirm("Are you sure you want to leave this squad?")) return;
    try {
      await apiService.leaveSquad(squadId);
      await fetchProblemSquads();
    } catch (e: any) {
      alert(e.message || 'Failed to leave squad');
    }
  };

  const handleShowIntelligence = async (mode: 'explain' | 'prototype') => {
    setIsOverlayOpen(true);
    if (mode === 'explain' && explanationData) return;
    if (mode === 'prototype' && prototypeData) return;

    setOverlayLoading(true);
    try {
      const [expl, proto] = await Promise.all([
        explanationData ? Promise.resolve(explanationData) : apiService.getExplanation(problem?.id || ''),
        mode === 'prototype' ? apiService.getPrototype(problem?.id || '') : Promise.resolve(prototypeData)
      ]);
      setExplanationData(expl);
      if (proto) setPrototypeData(proto);
    } catch (error) {
      console.error("Failed to fetch intelligence", error);
    } finally {
      setOverlayLoading(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-white/10 border-t-white rounded-full animate-spin" />
    </div>
  );

  if (!problem) return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-6 text-center">
      <h1 className="text-2xl font-bold mb-4">Problem not found</h1>
      <Link to="/dashboard" className="px-6 py-2 bg-white text-black rounded-full font-bold">Back to Shelf</Link>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Top Nav */}
      <nav className="sticky top-0 z-20 border-b border-white/5 bg-black/80 backdrop-blur-md">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-2 text-white/50 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Shelf</span>
          </Link>
          <div className="flex items-center gap-4">
            <button
              onClick={handleToggleInterest}
              disabled={loadingInterest}
              className={`p-2 transition-colors ${interested ? 'text-red-500' : 'text-white/50 hover:text-white'}`}
            >
              {loadingInterest ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Heart className={`w-5 h-5 ${interested ? 'fill-current' : ''}`} />
              )}
            </button>
            {/* Removed top nav collab buttons as they are now handled below */}
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-6 py-12 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Left Column: Brief */}
          <div className="lg:col-span-2 space-y-12">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className={`px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border border-white/10 bg-white/5`}>
                  {problem.difficulty}
                </span>
                <span className="text-white/30 text-xs flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Found {new Date(problem.createdAt).toLocaleDateString()}
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-black mb-6 leading-tight">
                {problem.title}
              </h1>
              <div className="flex flex-wrap gap-2 mb-8">
                {problem.techStack.map(tech => (
                  <span key={tech} className="px-4 py-1.5 bg-white/5 rounded-lg border border-white/5 text-sm font-medium text-white/70">
                    {tech}
                  </span>
                ))}
              </div>
            </div>

            <section className="space-y-6">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-widest text-white/30 mb-4 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Context
                </h3>
                <p className="text-xl text-white/80 leading-relaxed font-light">
                  {problem.humanExplanation}
                </p>
              </div>

              <div className="p-8 rounded-2xl bg-[#090909] border border-white/5">
                <h3 className="text-sm font-bold uppercase tracking-widest text-white/30 mb-4">Original Problem Statement</h3>
                <p className="text-white/50 leading-relaxed italic">
                  "{problem.description}"
                </p>
                <a
                  href={problem.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-6 inline-flex items-center gap-2 text-cyan-500 text-sm font-bold group"
                >
                  View Original Post on {problem.source}
                  <ExternalLink className="w-4 h-4 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                </a>
              </div>
            </section>

            {/* Smart Roadmap (Groq) */}
            <section className="p-8 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-transparent border border-cyan-500/20">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-cyan-400" />
                  AI Discovery & Execution
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => handleShowIntelligence('explain')}
                  className="p-6 bg-white/5 hover:bg-white/10 border border-white/5 rounded-2xl text-left transition-all group"
                >
                  <BarChart3 className="w-6 h-6 text-cyan-400 mb-4 group-hover:scale-110 transition-transform" />
                  <h4 className="font-bold mb-1">Explain Intelligence</h4>
                  <p className="text-xs text-white/40">View the heuristic breakdown of why this problem ranks for high impact.</p>
                </button>

                <button
                  onClick={() => handleShowIntelligence('prototype')}
                  className="p-6 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 rounded-2xl text-left transition-all group"
                >
                  <Zap className="w-6 h-6 text-cyan-400 mb-4 group-hover:scale-110 transition-transform" />
                  <h4 className="font-bold mb-1 text-cyan-400">Launch Prototype</h4>
                  <p className="text-xs text-cyan-400/40">Generate a custom 3-step technical roadmap for MVP implementation.</p>
                </button>
              </div>
            </section>
          </div>

          {/* Right Column: Stats & Meta */}
          <div className="space-y-8">
            <div className="p-6 rounded-2xl bg-[#090909] border border-white/5">
              <h3 className="text-xs font-bold uppercase tracking-widest text-white/30 mb-6">Metrics</h3>
              <div className="space-y-6">
                <button
                  onClick={handleToggleInterest}
                  disabled={loadingInterest}
                  className="w-full flex items-center justify-between group"
                >
                  <span className={`text-sm flex items-center gap-2 transition-colors ${interested ? 'text-red-500' : 'text-white/50 group-hover:text-white'}`}>
                    <Heart className={`w-4 h-4 ${interested ? 'fill-current' : ''}`} />
                    {interested ? 'Interested' : 'Mark as Interested'}
                  </span>
                  <span className="font-bold">{count}</span>
                </button>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/50 flex items-center gap-2">
                    <Users className="w-4 h-4" /> Active Squads
                  </span>
                  <span className="font-bold">{squads.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/50 flex items-center gap-2">
                    <Layers className="w-4 h-4" /> Solution Type
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${problem.solutionType === SolutionType.SOFTWARE ? 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20' :
                    problem.solutionType === SolutionType.HARDWARE ? 'bg-orange-500/10 text-orange-500 border-orange-500/20' :
                      'bg-purple-500/10 text-purple-500 border-purple-500/20'
                    }`}>
                    {problem.solutionType}
                  </span>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-[#090909] border border-white/5">
              <h3 className="text-xs font-bold uppercase tracking-widest text-white/30 mb-6">Recommended Skills</h3>
              <div className="flex flex-wrap gap-2">
                {['System Design', 'API Integration', 'UI/UX', ...problem.techStack.slice(0, 2)].map(skill => (
                  <span key={skill} className="px-3 py-1 bg-white/5 rounded-full text-xs text-white/40">
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-6 rounded-2xl bg-[#090909] border border-white/5">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xs font-bold uppercase tracking-widest text-white/30 flex items-center gap-2">
                  <Users className="w-4 h-4" /> Problem Squads
                </h3>
                <button
                  onClick={() => setShowCreateSquad(!showCreateSquad)}
                  className="p-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-500 rounded-lg transition-colors border border-cyan-500/20"
                  title="Create a new squad"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              {showCreateSquad && (
                <form onSubmit={handleCreateSquad} className="mb-6 p-4 border border-cyan-500/20 bg-cyan-500/5 rounded-xl">
                  <h4 className="text-sm font-bold text-cyan-400 mb-3">Create New Squad</h4>
                  <input
                    type="text"
                    placeholder="Squad Name"
                    className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white mb-3 focus:outline-none focus:border-cyan-500/50"
                    value={createForm.name}
                    onChange={e => setCreateForm(prev => ({ ...prev, name: e.target.value }))}
                    maxLength={50}
                    required
                  />
                  <textarea
                    placeholder="Squad Goals & Description"
                    className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50 resize-none h-20 mb-3"
                    value={createForm.description}
                    onChange={e => setCreateForm(prev => ({ ...prev, description: e.target.value }))}
                    maxLength={500}
                    required
                  />
                  <div className="flex justify-end gap-2">
                    <button type="button" onClick={() => setShowCreateSquad(false)} className="px-3 py-1.5 text-xs font-bold text-white/50 hover:text-white">Cancel</button>
                    <button type="submit" disabled={creatingSquad} className="px-3 py-1.5 bg-cyan-600 text-white rounded-lg text-xs font-bold hover:bg-cyan-500 flex items-center gap-1">
                      {creatingSquad ? <Loader2 className="w-3 h-3 animate-spin"/> : <Send className="w-3 h-3"/>} Create
                    </button>
                  </div>
                </form>
              )}

              <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                {loadingSquads ? (
                  <div className="flex justify-center py-4"><Loader2 className="w-5 h-5 animate-spin text-white/30" /></div>
                ) : squads.length === 0 ? (
                  <div className="text-center py-6 border border-dashed border-white/10 rounded-xl">
                    <p className="text-xs text-white/40 mb-2">No squads have been formed yet.</p>
                    <button onClick={() => setShowCreateSquad(true)} className="text-cyan-400 text-xs font-bold hover:underline">Be the first to create one!</button>
                  </div>
                ) : (
                  squads.map(sq => (
                    <div key={sq.id} className="p-4 bg-white/[0.02] border border-white/5 rounded-xl hover:border-white/10 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-sm text-white/90">{sq.name}</h4>
                        <span className="text-[10px] font-bold px-2 py-0.5 bg-white/10 rounded-full">{sq.member_count} Members</span>
                      </div>
                      <p className="text-xs text-white/50 mb-4 line-clamp-2">{sq.description || "No description provided."}</p>
                      
                      <div className="flex justify-between items-center mt-2">
                        <span className="text-[10px] text-white/30">Leader: @{sq.leader_username || 'Unknown'}</span>
                        
                        <div className="flex items-center gap-2">
                          {sq.is_leader ? (
                            <>
                              <Link to={`/squads/${sq.id}/chat`} className="text-[10px] font-bold px-3 py-1 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-md hover:bg-cyan-500/20">
                                Open Chat
                              </Link>
                              <button 
                                onClick={() => handleDeleteSquad(sq.id)}
                                className="p-1 bg-red-500/10 text-red-500 border border-red-500/20 rounded-md hover:bg-red-500/20"
                                title="Delete Squad"
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            </>
                          ) : sq.is_member || sq.user_request_status === 'accepted' ? (
                            <>
                              <Link to={`/squads/${sq.id}/chat`} className="text-[10px] font-bold px-3 py-1 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-md hover:bg-cyan-500/20">
                                Open Chat
                              </Link>
                              <button 
                                onClick={() => handleLeaveSquad(sq.id)}
                                className="p-1 bg-white/5 text-white/50 border border-white/10 rounded-md hover:bg-white/10 hover:text-white"
                                title="Leave Squad"
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            </>
                          ) : sq.user_request_status === 'pending' ? (
                            <span className="text-[10px] font-bold px-3 py-1 bg-yellow-500/10 text-yellow-500 border border-yellow-500/20 rounded-md">
                              Requested
                            </span>
                          ) : sq.user_request_status === 'rejected' ? (
                            <span className="text-[10px] font-bold px-3 py-1 bg-red-500/10 text-red-500 border border-red-500/20 rounded-md">
                              Rejected
                            </span>
                          ) : (
                            <button 
                              onClick={() => handleJoinSquad(sq.id)}
                              disabled={joiningId === sq.id}
                              className="text-[10px] font-bold px-3 py-1 bg-white text-black rounded-md hover:bg-white/80"
                            >
                              {joiningId === sq.id ? '...' : 'Join Squad'}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      <InferenceOverlay
        isOpen={isOverlayOpen}
        onClose={() => setIsOverlayOpen(false)}
        problemTitle={problem.title}
        explanationData={explanationData}
        prototypeData={prototypeData}
        loading={overlayLoading}
      />
    </div >
  );
};

// Clock helper moved to top

export default ProblemDetail;
