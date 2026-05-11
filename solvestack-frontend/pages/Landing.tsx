
import React from 'react';
import { Link } from 'react-router-dom';
import { Terminal, Zap, Users, Shield, ArrowRight, Star, Globe, MessageSquare, Code2, Sparkles, MoveRight } from 'lucide-react';

const Landing: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-cyan-500/30 overflow-x-hidden">
      {/* Subtle Grain Overlay for 'Classic' feel */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03] bg-[url('https://grainy-gradients.vercel.app/noise.svg')] z-50"></div>

      {/* Background decoration */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-cyan-900/20 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-purple-900/20 rounded-full blur-[120px]" />
      </div>

      <header className="relative z-10 container mx-auto px-6 py-10 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center group-hover:rotate-6 transition-transform shadow-[0_0_20px_rgba(255,255,255,0.1)]">
            <Terminal className="text-black w-6 h-6" />
          </div>
          <span className="text-2xl font-black tracking-tightest uppercase italic">SolveStack</span>
        </Link>
        
        <div className="hidden md:flex items-center gap-10 text-[11px] font-bold uppercase tracking-[0.2em] text-white/40">
          <Link to="/dashboard" className="hover:text-white transition-colors">The Shelf</Link>
          <a href="#" className="hover:text-white transition-colors">Manifesto</a>
          <a href="#" className="hover:text-white transition-colors">Sourcing</a>
        </div>

        <div className="flex items-center gap-6">
          <Link to="/login" className="text-xs font-bold uppercase tracking-widest text-white/40 hover:text-white transition-colors">Login</Link>
          <Link to="/register" className="px-6 py-2.5 bg-white text-black rounded-full text-xs font-black uppercase tracking-widest hover:bg-cyan-400 hover:scale-105 transition-all shadow-xl">
            Join the Squad
          </Link>
        </div>
      </header>

      <main className="relative z-10">
        {/* Hero Section */}
        <section className="container mx-auto px-6 pt-24 pb-32 text-center md:text-left flex flex-col md:flex-row items-center justify-between gap-16">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/10 bg-white/5 mb-8 backdrop-blur-sm">
              <Sparkles className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-[10px] font-bold tracking-[0.15em] uppercase text-white/60">Where real engineers find real work</span>
            </div>
            
            <h1 className="text-7xl md:text-[10rem] font-black leading-[0.85] mb-10 tracking-tighter italic">
              BUILD <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-white/80 to-white/20">WHAT'S NEEDED.</span>
            </h1>
            
            <p className="text-xl md:text-2xl text-white/40 max-w-xl mb-12 leading-relaxed font-medium">
              We scout the corners of the internet to find high-signal technical problems. No more "To-Do" apps. Start building solutions that people are actually asking for.
            </p>

            <div className="flex flex-col sm:flex-row gap-6">
              <Link to="/dashboard" className="group relative px-10 py-5 bg-white text-black rounded-2xl text-lg font-black flex items-center justify-center gap-3 overflow-hidden transition-all hover:shadow-[0_0_30px_rgba(255,255,255,0.2)]">
                Explore The Shelf
                <MoveRight className="w-5 h-5 group-hover:translate-x-2 transition-transform" />
              </Link>
              <button className="px-10 py-5 bg-black border border-white/10 text-white rounded-2xl text-lg font-bold hover:bg-white/5 transition-all">
                The Methodology
              </button>
            </div>
          </div>

          <div className="hidden lg:block w-full max-w-sm">
            <div className="relative p-1 bg-gradient-to-br from-white/20 to-transparent rounded-[2rem] transform rotate-3 hover:rotate-0 transition-transform duration-700">
               <div className="bg-[#090909] rounded-[1.8rem] p-8 space-y-6">
                  <div className="flex justify-between items-start">
                    <div className="px-3 py-1 bg-red-500/10 text-red-500 border border-red-500/20 rounded text-[9px] font-black uppercase">Advanced</div>
                    <Star className="w-4 h-4 text-white/20" />
                  </div>
                  <h3 className="text-2xl font-bold tracking-tight">Decentralized Tab Sync</h3>
                  <p className="text-sm text-white/40 leading-relaxed italic">"Why can't I sync my browser tabs locally via WiFi without using Google/Firefox cloud? It feels like a massive privacy leak."</p>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-2 py-1 bg-white/5 rounded text-[10px] font-bold text-white/60">Rust</span>
                    <span className="px-2 py-1 bg-white/5 rounded text-[10px] font-bold text-white/60">WebRTC</span>
                  </div>
                  <div className="pt-4 border-t border-white/5 flex justify-between items-center">
                    <span className="text-[10px] text-white/20 uppercase font-black">Sourced from StackOverflow</span>
                    <div className="flex -space-x-2">
                      <div className="w-6 h-6 rounded-full bg-cyan-500 border-2 border-black"></div>
                      <div className="w-6 h-6 rounded-full bg-purple-500 border-2 border-black"></div>
                    </div>
                  </div>
               </div>
            </div>
          </div>
        </section>

        {/* Live Problem Ticker - 'Personality' feature */}
        <div className="w-full bg-white/5 border-y border-white/5 py-6 overflow-hidden flex whitespace-nowrap group">
          <div className="flex animate-marquee group-hover:pause-animation gap-16 px-8 items-center">
            {[1,2,3,4,5].map(i => (
              <React.Fragment key={i}>
                <div className="flex items-center gap-4">
                  <span className="text-cyan-400 font-black">#SOLVED</span>
                  <span className="text-sm font-bold uppercase tracking-widest text-white/60">Quantized LLM Orchestrator</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-purple-400 font-black italic">NEW</span>
                  <span className="text-sm font-bold uppercase tracking-widest text-white/60">Cross-Browser P2P Sync</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-yellow-400 font-black underline">TRENDING</span>
                  <span className="text-sm font-bold uppercase tracking-widest text-white/60">ML Soil Sensor Grid</span>
                </div>
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Feature Grid: Sourcing Methodology */}
        <section className="container mx-auto px-6 py-32">
          <div className="max-w-2xl mb-20">
            <h2 className="text-4xl md:text-5xl font-black mb-6 tracking-tight italic">THE ANATOMY OF A PROBLEM</h2>
            <p className="text-white/40 text-lg leading-relaxed">
              We don't just scrape; we curate. Our backend transforms raw human frustration into architectural blueprints.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-12">
             <div className="space-y-6">
                <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
                  <Globe className="w-8 h-8 text-cyan-400" />
                </div>
                <h4 className="text-xl font-black italic uppercase tracking-tight">01. Discovery</h4>
                <p className="text-white/40 text-sm leading-relaxed">Real-time monitoring of technical forums, StackOverflow's unanswered queue, and Hacker News show HN.</p>
             </div>
             <div className="space-y-6">
                <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
                  <Code2 className="w-8 h-8 text-purple-400" />
                </div>
                <h4 className="text-xl font-black italic uppercase tracking-tight">02. Translation</h4>
                <p className="text-white/40 text-sm leading-relaxed">AI analyzes the sentiment and technical difficulty, generating suggested tech stacks and humanized summaries.</p>
             </div>
             <div className="space-y-6">
                <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
                  <Users className="w-8 h-8 text-yellow-400" />
                </div>
                <h4 className="text-xl font-black italic uppercase tracking-tight">03. Collaboration</h4>
                <p className="text-white/40 text-sm leading-relaxed">Once enough interest is registered, squads are automatically formed to bridge the gap from idea to MVP.</p>
             </div>
          </div>
        </section>

        {/* Classic Footer Section */}
        <section className="container mx-auto px-6 py-32 border-t border-white/5 flex flex-col md:flex-row justify-between gap-20">
           <div className="max-w-md">
             <h3 className="text-3xl font-black mb-8 italic">READY TO BUILD?</h3>
             <p className="text-white/30 text-sm leading-relaxed mb-8">
               SolveStack is currently in private beta. Join thousands of developers who have stopped building clones and started solving real problems.
             </p>
             <Link to="/register" className="inline-flex items-center gap-4 text-cyan-400 font-black tracking-widest uppercase text-xs group">
               Begin Your Journey
               <ArrowRight className="w-4 h-4 group-hover:translate-x-2 transition-transform" />
             </Link>
           </div>
           
           <div className="grid grid-cols-2 md:grid-cols-3 gap-12 text-xs font-bold uppercase tracking-widest text-white/20">
              <div className="space-y-4">
                <span className="text-white/40">Platform</span>
                <a href="#" className="block hover:text-white transition-colors">The Shelf</a>
                <a href="#" className="block hover:text-white transition-colors">Squads</a>
                <a href="#" className="block hover:text-white transition-colors">Leaderboard</a>
              </div>
              <div className="space-y-4">
                <span className="text-white/40">Social</span>
                <a href="#" className="block hover:text-white transition-colors">Twitter</a>
                <a href="#" className="block hover:text-white transition-colors">Discord</a>
                <a href="#" className="block hover:text-white transition-colors">Github</a>
              </div>
              <div className="space-y-4">
                <span className="text-white/40">Legal</span>
                <a href="#" className="block hover:text-white transition-colors">Privacy</a>
                <a href="#" className="block hover:text-white transition-colors">Terms</a>
              </div>
           </div>
        </section>
      </main>

      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee {
          animation: marquee 30s linear infinite;
        }
        .pause-animation {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
};

export default Landing;
