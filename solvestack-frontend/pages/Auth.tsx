
import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Terminal, ArrowRight, Github, Chrome } from 'lucide-react';

import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Auth: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();
  const isLogin = location.pathname === '/login';

  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        const response = await apiService.login(email, password);
        // Login successful, get user info (mock or fetch me)
        const userData = { email }; // For now just basic
        login(response.access_token, userData);
        navigate('/dashboard');
      } else {
        await apiService.register(username, email, password);
        // Auto login after register or ask to login
        const response = await apiService.login(email, password);
        const userData = { email, username };
        login(response.access_token, userData);
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <Link to="/" className="inline-flex items-center gap-2 mb-8">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
              <Terminal className="text-black w-6 h-6" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">SolveStack</span>
          </Link>
          <h2 className="text-3xl font-black text-white mb-2">
            {isLogin ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p className="text-white/40 text-sm">
            {isLogin
              ? 'Enter your credentials to access the Problem Shelf.'
              : 'Join a global squad of developers solving real problems.'}
          </p>
        </div>

        <div className="bg-[#090909] border border-white/5 rounded-3xl p-8 shadow-2xl">
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-sm font-medium">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLogin && (
              <div>
                <label className="block text-xs font-bold uppercase tracking-widest text-white/30 mb-2">Username</label>
                <input
                  type="text"
                  className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-white/30 transition-all text-white"
                  placeholder="johndoe"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-bold uppercase tracking-widest text-white/30 mb-2">Email Address</label>
              <input
                type="email"
                className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-white/30 transition-all text-white"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-widest text-white/30 mb-2">Password</label>
              <input
                type="password"
                className="w-full bg-black border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-white/30 transition-all text-white"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button className="w-full py-4 bg-white text-black font-bold rounded-xl hover:bg-white/90 transition-all flex items-center justify-center gap-2 group">
              {isLogin ? 'Sign In' : 'Get Started'}
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </form>

          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-white/5"></div></div>
            <div className="relative flex justify-center text-xs uppercase tracking-widest font-bold"><span className="bg-[#090909] px-4 text-white/20">or continue with</span></div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <button className="flex items-center justify-center gap-2 py-3 border border-white/5 bg-white/5 rounded-xl hover:bg-white/10 transition-all">
              <Github className="w-4 h-4" />
              <span className="text-xs font-bold">GitHub</span>
            </button>
            <button className="flex items-center justify-center gap-2 py-3 border border-white/5 bg-white/5 rounded-xl hover:bg-white/10 transition-all">
              <Chrome className="w-4 h-4" />
              <span className="text-xs font-bold">Google</span>
            </button>
          </div>
        </div>

        <p className="text-center text-sm text-white/30">
          {isLogin ? "Don't have an account?" : "Already have an account?"}{' '}
          <Link to={isLogin ? '/register' : '/login'} className="text-white font-bold hover:underline">
            {isLogin ? 'Sign Up' : 'Sign In'}
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Auth;
