import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import {
  ArrowLeft, Users, Crown, Send, Loader2, MessageSquare,
  ChevronRight, ChevronLeft, Wifi, WifiOff, Trash, LogOut
} from 'lucide-react';

const WS_BASE = 'ws://localhost:8000';

interface ChatMessage {
  id: number;
  sender_id: number;
  sender_username: string;
  content: string;
  sent_at: string;
}

interface SquadDetail {
  id: number;
  name: string;
  description: string;
  problem_id: number;
  problem_title: string;
  leader_id: number;
  leader_username: string;
  members: { id: number; username: string }[];
  is_member: boolean;
  is_leader: boolean;
}

const SquadChat: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const squadId = parseInt(id || '0');

  const [squad, setSquad] = useState<SquadDetail | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const [showMembers, setShowMembers] = useState(true);

  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const token = localStorage.getItem('token');

  // Decode current user id from JWT
  const currentUserId = (() => {
    try {
      if (!token) return null;
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload?.id ?? null;
    } catch { return null; }
  })();

  const scrollToBottom = useCallback(() => {
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 60);
  }, []);

  useEffect(() => {
    if (!token) { navigate('/login'); return; }

    const init = async () => {
      try {
        const [detail, history] = await Promise.all([
          apiService.getSquadDetail(squadId),
          apiService.getSquadMessages(squadId)
        ]);

        if (!detail.is_member) {
          navigate('/squads');
          return;
        }
        setSquad(detail);
        setMessages(history);
        scrollToBottom();
      } catch {
        navigate('/squads');
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [squadId, token, navigate, scrollToBottom]);

  // WebSocket connection
  useEffect(() => {
    if (!token || loading) return;

    const ws = new WebSocket(`${WS_BASE}/ws/squad/${squadId}?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (event) => {
      const msg: ChatMessage = JSON.parse(event.data);
      setMessages(prev => {
        // Avoid duplicates
        if (prev.some(m => m.id === msg.id)) return prev;
        return [...prev, msg];
      });
      scrollToBottom();
    };

    return () => {
      ws.close();
    };
  }, [squadId, token, loading, scrollToBottom]);

  const sendMessage = () => {
    const content = input.trim();
    if (!content || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ content }));
    setInput('');
    inputRef.current?.focus();
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to permanently delete this squad? This action cannot be undone.")) return;
    try {
      await apiService.deleteSquad(squadId);
      navigate('/squads');
    } catch (e: any) {
      alert(e.message || 'Failed to delete squad');
    }
  };

  const handleLeave = async () => {
    if (!window.confirm("Are you sure you want to leave this squad?")) return;
    try {
      await apiService.leaveSquad(squadId);
      navigate('/squads');
    } catch (e: any) {
      alert(e.message || 'Failed to leave squad');
    }
  };


  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  // Group messages by day
  const grouped: { date: string; msgs: ChatMessage[] }[] = [];
  for (const msg of messages) {
    const date = formatDate(msg.sent_at);
    const last = grouped[grouped.length - 1];
    if (last && last.date === date) last.msgs.push(msg);
    else grouped.push({ date, msgs: [msg] });
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
      </div>
    );
  }

  if (!squad) return null;

  return (
    <div className="h-screen bg-[#050505] text-white flex flex-col">
      {/* Header */}
      <header className="border-b border-white/5 bg-black/60 backdrop-blur-xl flex-shrink-0 px-6 h-16 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <Link to="/squads" className="p-2 hover:bg-white/5 rounded-full transition-colors">
            <ArrowLeft className="w-5 h-5 text-white/40" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-base leading-tight">{squad.name}</h1>
              {squad.is_leader && <Crown className="w-4 h-4 text-amber-400" title="You lead this squad" />}
            </div>
            <p className="text-xs text-white/30 truncate max-w-xs">{squad.problem_title}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest ${connected ? 'text-green-400' : 'text-white/20'}`}>
            {connected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {connected ? 'Live' : 'Offline'}
          </span>
          <button
            onClick={() => setShowMembers(v => !v)}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 bg-white/5 rounded-xl text-xs font-bold hover:bg-white/10 transition-all"
          >
            <Users className="w-3.5 h-3.5" />
            {squad.members.length}
            {showMembers ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
          </button>
          
          {squad.is_leader ? (
            <button
              onClick={handleDelete}
              className="p-1.5 bg-red-500/10 text-red-500 rounded-xl hover:bg-red-500/20 transition-colors"
              title="Delete Squad"
            >
              <Trash className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleLeave}
              className="p-1.5 bg-white/5 text-white/50 rounded-xl hover:bg-white/10 hover:text-white transition-colors"
              title="Leave Squad"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Messages */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Message list */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-1 scroll-smooth">
            {grouped.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-20">
                <MessageSquare className="w-12 h-12 text-white/10 mb-4" />
                <p className="text-white/30 text-sm">No messages yet. Say hello to your squad! 👋</p>
              </div>
            ) : (
              grouped.map(group => (
                <div key={group.date}>
                  {/* Date separator */}
                  <div className="flex items-center gap-3 my-4">
                    <div className="flex-1 h-px bg-white/5" />
                    <span className="text-[10px] text-white/20 font-bold uppercase tracking-widest px-2">{group.date}</span>
                    <div className="flex-1 h-px bg-white/5" />
                  </div>
                  {group.msgs.map((msg, idx) => {
                    const isSelf = msg.sender_id === currentUserId;
                    const showHeader = idx === 0 || group.msgs[idx - 1].sender_id !== msg.sender_id;
                    return (
                      <div key={msg.id} className={`flex gap-2 items-end ${isSelf ? 'flex-row-reverse' : 'flex-row'} ${!showHeader ? 'mt-0.5' : 'mt-3'}`}>
                        {/* Avatar */}
                        {showHeader && !isSelf && (
                          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-500/30 to-purple-500/30 flex items-center justify-center flex-shrink-0 mb-1">
                            <span className="text-[10px] font-bold text-white/60">{msg.sender_username[0].toUpperCase()}</span>
                          </div>
                        )}
                        {!showHeader && !isSelf && <div className="w-7 flex-shrink-0" />}

                        <div className={`max-w-[70%] ${isSelf ? 'items-end' : 'items-start'} flex flex-col gap-0.5`}>
                          {showHeader && !isSelf && (
                            <span className="text-[10px] text-white/30 font-bold ml-1">
                              {msg.sender_username}
                              {msg.sender_id === squad.leader_id && <Crown className="inline w-3 h-3 text-amber-400 ml-1" />}
                            </span>
                          )}
                          <div className={`px-4 py-2 rounded-2xl text-sm leading-relaxed break-words ${
                            isSelf
                              ? 'bg-cyan-500 text-black font-medium rounded-br-sm'
                              : 'bg-white/[0.07] text-white rounded-bl-sm'
                          }`}>
                            {msg.content}
                          </div>
                          <span className={`text-[9px] text-white/20 mx-1 ${isSelf ? 'text-right' : 'text-left'}`}>
                            {formatTime(msg.sent_at)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ))
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input bar */}
          <div className="flex-shrink-0 border-t border-white/5 bg-black/40 backdrop-blur-xl px-6 py-4">
            <div className="flex items-center gap-3">
              <input
                ref={inputRef}
                type="text"
                placeholder={connected ? 'Type a message...' : 'Connecting...'}
                className="flex-1 bg-white/[0.05] border border-white/10 rounded-2xl px-5 py-3 text-sm focus:outline-none focus:border-white/20 placeholder:text-white/20 transition-all"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendMessage()}
                disabled={!connected}
              />
              <button
                onClick={sendMessage}
                disabled={!connected || !input.trim()}
                className="w-11 h-11 flex-shrink-0 bg-cyan-500 hover:bg-cyan-400 disabled:bg-white/5 disabled:text-white/20 text-black rounded-2xl flex items-center justify-center transition-all"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Members Sidebar */}
        {showMembers && (
          <aside className="hidden md:flex w-64 flex-col border-l border-white/5 bg-black/30 flex-shrink-0 overflow-y-auto">
            <div className="p-5 border-b border-white/5">
              <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">Members — {squad.members.length}</p>
            </div>
            <div className="p-3 space-y-1">
              {squad.members.map(m => (
                <div key={m.id} className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-white/5 transition-colors">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-500/30 to-purple-500/30 flex items-center justify-center flex-shrink-0">
                    <span className="text-[10px] font-bold text-white/60">{m.username[0].toUpperCase()}</span>
                  </div>
                  <span className="text-sm truncate text-white/70">{m.username}</span>
                  {m.id === squad.leader_id && <Crown className="w-3.5 h-3.5 text-amber-400 ml-auto flex-shrink-0" />}
                </div>
              ))}
            </div>
            {/* Squad description */}
            {squad.description && (
              <div className="mt-auto p-4 border-t border-white/5">
                <p className="text-[10px] font-bold uppercase tracking-widest text-white/20 mb-1.5">About</p>
                <p className="text-xs text-white/40 leading-relaxed">{squad.description}</p>
              </div>
            )}
          </aside>
        )}
      </div>
    </div>
  );
};

export default SquadChat;
