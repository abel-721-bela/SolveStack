
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Terminal, ArrowRight, Sparkles } from 'lucide-react';

const Welcome: React.FC = () => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center relative overflow-hidden selection:bg-cyan-500/30">
      {/* Dynamic Background Elements */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/5 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute top-1/4 right-1/4 w-[300px] h-[300px] bg-purple-500/5 rounded-full blur-[100px]" />
        {/* Grid Overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)]" />
      </div>

      <div className={`relative z-10 transition-all duration-1000 transform ${mounted ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'} text-center px-6`}>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 mb-8 backdrop-blur-sm">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/60">V1.0 Early Access</span>
        </div>

        <div className="flex items-center justify-center gap-4 mb-6">
           <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-[0_0_30px_rgba(255,255,255,0.2)]">
             <Terminal className="text-black w-10 h-10" />
           </div>
        </div>

        <h1 className="text-7xl md:text-9xl font-black tracking-tighter mb-4 leading-none italic">
          SOLVE<span className="text-transparent bg-clip-text bg-gradient-to-b from-white to-white/20">STACK</span>
        </h1>

        <p className="text-lg md:text-xl text-white/40 max-w-lg mx-auto mb-12 font-medium tracking-tight">
          The curated <span className="text-white/80">Problem Shelf</span> where real-world technical challenges find their creators.
        </p>

        <div className="flex flex-col items-center gap-6">
          <Link 
            to="/landing" 
            className="group relative px-10 py-5 bg-white text-black rounded-full text-lg font-black flex items-center gap-3 overflow-hidden transition-all hover:scale-105 active:scale-95"
          >
            <span className="relative z-10">Enter Platform</span>
            <ArrowRight className="relative z-10 w-5 h-5 group-hover:translate-x-1 transition-transform" />
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-purple-400 opacity-0 group-hover:opacity-10 transition-opacity" />
          </Link>
          
          <div className="flex items-center gap-8 text-[11px] font-bold uppercase tracking-widest text-white/20">
            <span className="flex items-center gap-2"><div className="w-1 h-1 bg-purple-500 rounded-full" /> StackOverflow Sync</span>
            <span className="flex items-center gap-2"><div className="w-1 h-1 bg-yellow-500 rounded-full" /> HN Discovery</span>
          </div>
        </div>
      </div>

      {/* Aesthetic Footer Detail */}
      <div className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-4 opacity-30">
        <div className="w-px h-12 bg-gradient-to-b from-white to-transparent" />
        <span className="text-[10px] font-mono uppercase tracking-[0.3em]">Scroll to learn more</span>
      </div>
    </div>
  );
};

export default Welcome;
