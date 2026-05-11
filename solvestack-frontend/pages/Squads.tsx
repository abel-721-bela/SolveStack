import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import {
  Users, ArrowLeft, Plus, MessageSquare, Loader2, Check, X,
  Crown, Clock, ChevronRight, Search, Zap, Send, Trash2, LogOut
} from 'lucide-react';

interface Squad {
  id: number;
  name: string;
  description: string;
  problem_id: number;
  problem_title: string;
  leader_id: number;
  leader_username: string;
  member_count: number;
  pending_requests: number;
  user_request_status?: string | null;
  created_at: string;
}

const Squads: React.FC = () => {
  const navigate = useNavigate();
  const [squads, setSquads] = useState<Squad[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [joiningId, setJoiningId] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState<{ [key: string]: boolean }>({});

  // Create form state
  const [problems, setProblems] = useState<any[]>([]);
  const [createForm, setCreateForm] = useState({ problem_id: '', name: '', description: '' });
  const [creating, setCreating] = useState(false);

  const token = localStorage.getItem('token');
  const currentUserId = (() => {
    try {
      if (!token) return null;
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload?.id ?? null;
    } catch { return null; }
  })();

  const fetchSquads = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiService.getSquads();
      // Enrich with user-specific request status if logged in
      if (token) {
        const enriched = await Promise.all(data.map(async (sq: Squad) => {
          try {
            const detail = await apiService.getSquadDetail(sq.id);
            return { ...sq, user_request_status: detail.user_request_status, pending_requests: detail.pending_requests ?? sq.pending_requests, is_leader: detail.is_leader, is_member: detail.is_member };
          } catch { return sq; }
        }));
        setSquads(enriched as any);
      } else {
        setSquads(data);
      }
    } catch (e) {
      console.error("Failed to load squads", e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchSquads(); }, [fetchSquads]);

  useEffect(() => {
    if (showCreate) {
      apiService.getProblems(0, 50).then(setProblems);
    }
  }, [showCreate]);

  const handleJoin = async (squadId: number) => {
    if (!token) { navigate('/login'); return; }
    setJoiningId(squadId);
    try {
      await apiService.joinSquad(squadId);
      await fetchSquads();
    } catch (e: any) {
      alert(e.message || 'Failed to send join request');
    } finally {
      setJoiningId(null);
    }
  };

  const handleAccept = async (squadId: number, userId: number) => {
    const key = `accept-${squadId}-${userId}`;
    setActionLoading(prev => ({ ...prev, [key]: true }));
    try {
      await apiService.acceptSquadMember(squadId, userId);
      await fetchSquads();
    } finally {
      setActionLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleReject = async (squadId: number, userId: number) => {
    const key = `reject-${squadId}-${userId}`;
    setActionLoading(prev => ({ ...prev, [key]: true }));
    try {
      await apiService.rejectSquadMember(squadId, userId);
      await fetchSquads();
    } finally {
      setActionLoading(prev => ({ ...prev, [key]: false }));
    }
  };


  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.problem_id || !createForm.name.trim()) return;
    setCreating(true);
    try {
      const result = await apiService.createSquad(
        parseInt(createForm.problem_id),
        createForm.name.trim(),
        createForm.description.trim()
      );
      await fetchSquads();
      setShowCreate(false);
      setCreateForm({ problem_id: '', name: '', description: '' });
      navigate(`/squads/${result.id}/chat`);
    } catch (e: any) {
      alert(e.message || 'Failed to create squad');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (squadId: number) => {
    if (!window.confirm("Are you sure you want to delete this squad? This action cannot be undone and all chat history will be lost.")) return;
    const key = `delete-${squadId}`;
    setActionLoading(prev => ({ ...prev, [key]: true }));
    try {
      await apiService.deleteSquad(squadId);
      await fetchSquads();
    } catch (e: any) {
      alert(e.message || 'Failed to delete squad');
    } finally {
      setActionLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleLeave = async (squadId: number) => {
    if (!window.confirm("Are you sure you want to leave this squad?")) return;
    const key = `leave-${squadId}`;
    setActionLoading(prev => ({ ...prev, [key]: true }));
    try {
      await apiService.leaveSquad(squadId);
      await fetchSquads();
    } catch (e: any) {
      alert(e.message || 'Failed to leave squad');
    } finally {
      setActionLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const filtered = squads.filter(sq =>
    sq.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    sq.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    sq.problem_title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusButton = (sq: any) => {
    if (sq.is_leader) {
      return (
        <div className="flex gap-2">
          <Link
            to={`/squads/${sq.id}/chat`}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-black font-bold text-xs rounded-xl hover:bg-cyan-400 transition-all"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            Open Chat
          </Link>
          <button 
            onClick={() => handleDelete(sq.id)}
            className="p-2 bg-red-500/10 text-red-500 border border-red-500/20 rounded-xl hover:bg-red-500/20"
            title="Delete Squad"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      );
    }
    if (sq.is_member || sq.user_request_status === 'accepted') {
      return (
        <div className="flex gap-2">
          <Link
            to={`/squads/${sq.id}/chat`}
            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-black font-bold text-xs rounded-xl hover:bg-cyan-400 transition-all"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            Open Chat
          </Link>
          <button 
            onClick={() => handleLeave(sq.id)}
            className="p-2 bg-white/5 text-white/50 border border-white/10 rounded-xl hover:bg-white/10 hover:text-white"
            title="Leave Squad"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      );
    }
    if (sq.user_request_status === 'pending') {
      return (
        <span className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 text-white/40 text-xs rounded-xl font-bold">
          <Clock className="w-3.5 h-3.5" />
          Request Pending
        </span>
      );
    }
    if (sq.user_request_status === 'rejected') {
      return (
        <span className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl font-bold">
          <X className="w-3.5 h-3.5" />
          Request Rejected
        </span>
      );
    }
    return (
      <button
        onClick={() => handleJoin(sq.id)}
        disabled={joiningId === sq.id}
        className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 text-white text-xs font-bold rounded-xl hover:bg-white/10 hover:border-cyan-500/30 transition-all disabled:opacity-50"
      >
        {joiningId === sq.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Users className="w-3.5 h-3.5" />}
        Join Squad
      </button>
    );
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Nav */}
      <nav className="border-b border-white/5 bg-black/50 backdrop-blur-md sticky top-0 z-20">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="p-2 hover:bg-white/5 rounded-full transition-colors">
              <ArrowLeft className="w-5 h-5 text-white/50" />
            </Link>
            <h1 className="text-xl font-bold tracking-tight">Squads</h1>
          </div>
          {token && (
            <button
              onClick={() => setShowCreate(v => !v)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${showCreate ? 'bg-white text-black' : 'bg-white/5 border border-white/10 hover:bg-white/10 text-white'}`}
            >
              <Plus className="w-4 h-4" />
              Start a Squad
            </button>
          )}
        </div>
      </nav>

      <main className="container mx-auto px-6 py-10 max-w-5xl">
        {/* Create Squad Panel */}
        {showCreate && (
          <div className="mb-10 p-8 bg-gradient-to-br from-cyan-500/10 to-transparent border border-cyan-500/20 rounded-3xl">
            <h2 className="text-lg font-bold mb-1 flex items-center gap-2"><Zap className="w-5 h-5 text-cyan-500" /> Start a New Squad</h2>
            <p className="text-sm text-white/40 mb-6">Describe your goals to attract like-minded collaborators.</p>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-white/40 mb-1 uppercase tracking-widest">Problem</label>
                <select
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-cyan-500/50 text-white"
                  value={createForm.problem_id}
                  onChange={e => setCreateForm(f => ({ ...f, problem_id: e.target.value }))}
                  required
                >
                  <option value="">Select a problem...</option>
                  {problems.map(p => (
                    <option key={p.id} value={p.id}>{p.title.substring(0, 80)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-white/40 mb-1 uppercase tracking-widest">Squad Name</label>
                <input
                  type="text"
                  placeholder="e.g. Memory Leak Hunters"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-cyan-500/50 text-white placeholder:text-white/20"
                  value={createForm.name}
                  onChange={e => setCreateForm(f => ({ ...f, name: e.target.value }))}
                  required
                  maxLength={120}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-white/40 mb-1 uppercase tracking-widest">Description & Goals</label>
                <textarea
                  rows={4}
                  placeholder="Describe your aims, what you want to build, and what kind of collaborators you're looking for..."
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-cyan-500/50 text-white placeholder:text-white/20 resize-none"
                  value={createForm.description}
                  onChange={e => setCreateForm(f => ({ ...f, description: e.target.value }))}
                  maxLength={800}
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={creating}
                  className="flex items-center gap-2 px-6 py-2.5 bg-cyan-500 text-black font-bold text-sm rounded-xl hover:bg-cyan-400 transition-all disabled:opacity-50"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  Create Squad
                </button>
                <button type="button" onClick={() => setShowCreate(false)} className="px-5 py-2.5 bg-white/5 rounded-xl text-sm font-bold hover:bg-white/10 transition-all">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Search */}
        <div className="relative mb-8">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
          <input
            type="text"
            placeholder="Search squads by name, description or problem..."
            className="w-full bg-white/[0.03] border border-white/10 rounded-2xl py-3.5 pl-12 pr-4 text-sm focus:outline-none focus:border-white/20 transition-all placeholder:text-white/20 text-white"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Squad List */}
        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 bg-[#090909] rounded-3xl border border-white/5 border-dashed">
            <Users className="w-12 h-12 text-white/10 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">No squads found</h2>
            <p className="text-white/40 text-sm max-w-xs mx-auto mb-6">
              {token ? 'Be the first! Start a squad for a problem you care about.' : 'Login to start or join a squad.'}
            </p>
            {token ? (
              <button onClick={() => setShowCreate(true)} className="px-6 py-2.5 bg-white text-black font-bold rounded-xl hover:bg-white/90 transition-all text-sm">
                Start a Squad
              </button>
            ) : (
              <Link to="/login" className="px-6 py-2.5 bg-white text-black font-bold rounded-xl hover:bg-white/90 transition-all text-sm">
                Log in
              </Link>
            )}
          </div>
        ) : (
          <div className="grid gap-5">
            {filtered.map(sq => (
              <div key={sq.id} className="p-6 bg-[#090909] border border-white/5 rounded-2xl hover:border-white/10 transition-all space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-xs font-bold text-white/40 uppercase tracking-widest">Problem:</span>
                      <span className="text-xs text-cyan-400/80 truncate">{sq.problem_title}</span>
                    </div>
                    <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                      {sq.name}
                      {(sq as any).is_leader && <Crown className="w-4 h-4 text-amber-400" title="You lead this squad" />}
                    </h3>
                    <p className="text-sm text-white/50 leading-relaxed line-clamp-2">{sq.description || 'No description provided.'}</p>
                  </div>
                  <div className="flex-shrink-0 flex items-center gap-2">
                    {getStatusButton(sq as any)}
                    {(sq as any).is_leader ? (
                      <button
                        onClick={() => handleDelete(sq.id)}
                        disabled={actionLoading[`delete-${sq.id}`]}
                        className="p-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 rounded-xl transition-colors disabled:opacity-50"
                        title="Delete Squad"
                      >
                        {actionLoading[`delete-${sq.id}`] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                      </button>
                    ) : (sq as any).is_member ? (
                      <button
                        onClick={() => handleLeave(sq.id)}
                        disabled={actionLoading[`leave-${sq.id}`]}
                        className="p-2 bg-white/5 text-white/50 hover:bg-white/10 hover:text-white rounded-xl transition-colors disabled:opacity-50"
                        title="Leave Squad"
                      >
                        {actionLoading[`leave-${sq.id}`] ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogOut className="w-4 h-4" />}
                      </button>
                    ) : null}
                  </div>
                </div>

                <div className="flex items-center gap-5 text-xs text-white/30 pt-2 border-t border-white/5">
                  <span className="flex items-center gap-1.5">
                    <Crown className="w-3.5 h-3.5 text-amber-400/60" />
                    {sq.leader_username}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5" />
                    {sq.member_count} member{sq.member_count !== 1 ? 's' : ''}
                  </span>
                </div>

                {/* Leader: pending join requests */}
                {(sq as any).is_leader && Array.isArray((sq as any).pending_requests) && (sq as any).pending_requests.length > 0 && (
                  <div className="pt-3 border-t border-white/5 space-y-2">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">Pending Join Requests</p>
                    {(sq as any).pending_requests.map((req: any) => (
                      <div key={req.request_id} className="flex items-center justify-between px-3 py-2 bg-white/5 rounded-xl">
                        <span className="text-sm font-medium text-white/70">{req.username}</span>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleAccept(sq.id, req.user_id)}
                            disabled={actionLoading[`accept-${sq.id}-${req.user_id}`]}
                            className="flex items-center gap-1 px-3 py-1 bg-green-500/20 text-green-400 text-xs font-bold rounded-lg hover:bg-green-500/30 transition-all disabled:opacity-50"
                          >
                            {actionLoading[`accept-${sq.id}-${req.user_id}`] ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                            Accept
                          </button>
                          <button
                            onClick={() => handleReject(sq.id, req.user_id)}
                            disabled={actionLoading[`reject-${sq.id}-${req.user_id}`]}
                            className="flex items-center gap-1 px-3 py-1 bg-red-500/20 text-red-400 text-xs font-bold rounded-lg hover:bg-red-500/30 transition-all disabled:opacity-50"
                          >
                            {actionLoading[`reject-${sq.id}-${req.user_id}`] ? <Loader2 className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
                            Reject
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default Squads;
