import React from 'react';
import { Terminal, Settings, LogOut, ChevronRight, Activity, ArrowLeft } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

const Profile: React.FC = () => {
  const { user, isAuthenticated, logout, refreshUser } = useAuth();

  React.useEffect(() => {
    if (isAuthenticated) {
      refreshUser();
    }
  }, []);

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-12 h-12 text-white/20 mx-auto mb-4 animate-pulse" />
          <p className="text-white/40 font-mono">Loading decrypted profile data...</p>
        </div>
      </div>
    );
  }

  const logoutAndRedirect = () => {
    logout();
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <nav className="border-b border-white/5 bg-black/50 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-6 h-16 flex items-center">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 text-white/40 hover:text-white transition-all text-sm font-medium group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Back to Problem Shelf
          </Link>
        </div>
      </nav>
      <header className="border-b border-white/5 py-12">
        <div className="container mx-auto px-6 max-w-5xl flex flex-col md:flex-row items-center gap-8">
          <div className="w-32 h-32 rounded-3xl bg-gradient-to-br from-cyan-500 to-purple-500 p-1">
            <div className="w-full h-full bg-black rounded-[22px] flex items-center justify-center">
              <Terminal className="w-12 h-12 text-white" />
            </div>
          </div>
          <div className="flex-1 text-center md:text-left">
            <h1 className="text-4xl font-black mb-2 tracking-tight">@{user.username} <span className="text-white/20 text-xs font-mono">#{user.id}</span></h1>
            <p className="text-white/40 mb-6 font-mono text-sm">{user.email}</p>
            <div className="flex flex-wrap justify-center md:justify-start gap-4">
              <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/5 rounded-xl">
                <span className="text-xl font-bold">{user.interested_count || 0}</span>
                <span className="text-xs uppercase tracking-widest text-white/30">Interested</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/5 rounded-xl">
                <span className="text-xl font-bold">{user.squads_count || 0}</span>
                <span className="text-xs uppercase tracking-widest text-white/30">Squads</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/5 rounded-xl">
                <span className="text-xl font-bold">{user.activity_score || 0}</span>
                <span className="text-xs uppercase tracking-widest text-white/30">Pulse</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="p-3 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 transition-all">
              <Settings className="w-5 h-5 text-white/50" />
            </button>
            <button
              onClick={logoutAndRedirect}
              className="p-3 bg-red-500/10 border border-red-500/10 rounded-xl hover:bg-red-500/20 transition-all"
            >
              <LogOut className="w-5 h-5 text-red-500" />
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12 max-w-5xl">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-1 space-y-8">
            <section>
              <h3 className="text-xs font-bold uppercase tracking-widest text-white/30 mb-4">Top Skills</h3>
              <div className="flex flex-wrap gap-2">
                {user.skills && user.skills.length > 0 ? (
                  user.skills.map(skill => (
                    <span key={skill} className="px-3 py-1 bg-[#111] border border-white/5 rounded-lg text-xs font-medium">
                      {skill}
                    </span>
                  ))
                ) : (
                  <p className="text-xs text-white/20 italic">No skills added yet.</p>
                )}
                <button className="px-3 py-1 bg-white/5 border border-white/10 border-dashed rounded-lg text-xs text-white/30 hover:text-white transition-all">+ Add Skill</button>
              </div>
            </section>

            <section>
              <h3 className="text-xs font-bold uppercase tracking-widest text-white/30 mb-4">Interests</h3>
              <div className="space-y-2">
                {user.interests && user.interests.length > 0 ? (
                  user.interests.map(interest => (
                    <div key={interest} className="p-3 bg-[#090909] border border-white/5 rounded-xl text-sm text-white/60">
                      {interest}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-white/20 italic">No interests specified.</p>
                )}
              </div>
            </section>
          </div>

          <div className="md:col-span-2 space-y-12">
            <section>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold">Active Squads</h3>
                <span className="text-xs text-cyan-400 font-mono">{user.squads_count || 0} Current Projects</span>
              </div>
              <div className="space-y-4">
                {(user.squads_count || 0) === 0 ? (
                  <div className="p-12 bg-[#090909] border border-white/5 border-dashed rounded-2xl flex flex-col items-center justify-center text-center">
                    <Activity className="w-12 h-12 text-white/10 mb-4" />
                    <p className="text-white/30 text-sm mb-4">You haven't joined any squads yet.</p>
                    <Link
                      to="/dashboard"
                      className="px-6 py-2 bg-white/5 border border-white/10 rounded-full text-xs font-bold hover:bg-white/10 transition-all shadow-lg shadow-black/20"
                    >
                      Browse Problems
                    </Link>
                  </div>
                ) : (
                  <p className="text-sm text-white/40 italic">Squad details integration coming soon in Phase 3.</p>
                )}
              </div>
            </section>

            <section>
              <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-500" />
                Contribution Pulse
              </h3>
              <div className="h-40 bg-[#090909] border border-white/5 rounded-2xl p-6 flex items-center justify-center text-white/20 italic text-sm">
                {user.username}'s contribution heatmap will appear here as activity grows.
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Profile;
