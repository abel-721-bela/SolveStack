import React from 'react';
import { X, Sparkles, Zap, Shield, Cpu, BarChart3, Loader2, CheckCircle2 } from 'lucide-react';

interface InferenceOverlayProps {
    isOpen: boolean;
    onClose: () => void;
    problemTitle: string;
    explanationData: any;
    prototypeData: any;
    loading: boolean;
}

const InferenceOverlay: React.FC<InferenceOverlayProps> = ({
    isOpen,
    onClose,
    problemTitle,
    explanationData,
    prototypeData,
    loading
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-6 bg-black/80 backdrop-blur-xl animate-in fade-in duration-300">
            <div className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden bg-[#0a0a0a] border border-white/10 rounded-3xl shadow-[0_0_50px_rgba(0,0,0,0.5)] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-white/5">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-cyan-500/10 rounded-xl flex items-center justify-center border border-cyan-500/20">
                            <Sparkles className="w-5 h-5 text-cyan-400" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white leading-tight">Project Intelligence</h2>
                            <p className="text-xs text-white/40 font-medium truncate max-w-[300px] md:max-w-md">{problemTitle}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/5 rounded-full transition-colors text-white/40 hover:text-white"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 md:p-8 custom-scrollbar">
                    {loading ? (
                        <div className="h-64 flex flex-col items-center justify-center gap-4">
                            <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
                            <p className="text-sm font-medium text-white/40 animate-pulse">Running Inference Engine...</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                            {/* Left Column: Metrics & Score */}
                            <div className="lg:col-span-2 space-y-8">
                                <div className="p-6 bg-white/[0.02] border border-white/5 rounded-2xl">
                                    <h3 className="text-xs font-bold uppercase tracking-widest text-white/30 mb-6 flex items-center gap-2">
                                        <BarChart3 className="w-4 h-4" />
                                        EI Score Breakdown
                                    </h3>
                                    <div className="space-y-5">
                                        {explanationData?.breakdown && Object.entries(explanationData.breakdown).map(([key, val]: [string, any]) => (
                                            <div key={key} className="space-y-2">
                                                <div className="flex justify-between items-center text-xs">
                                                    <span className="capitalize text-white/60 font-medium">{key}</span>
                                                    <span className="text-white font-bold">{(val * 100).toFixed(0)}%</span>
                                                </div>
                                                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-1000"
                                                        style={{ width: `${val * 100}%` }}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                        <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                                            <span className="text-sm font-bold text-white">Overall EIS</span>
                                            <span className="text-2xl font-black text-white">{explanationData?.engineering_impact_score?.toFixed(0)}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-6 bg-cyan-500/5 border border-cyan-500/10 rounded-2xl">
                                    <h3 className="text-xs font-bold uppercase tracking-widest text-cyan-400/50 mb-4 flex items-center gap-2">
                                        <Zap className="w-4 h-4" />
                                        Heuristic Verdict
                                    </h3>
                                    <p className="text-sm text-cyan-50/70 leading-relaxed font-medium">
                                        {explanationData?.explanation}
                                    </p>
                                </div>
                            </div>

                            {/* Right Column: AI Plan */}
                            <div className="lg:col-span-3 space-y-6">
                                <div className="flex items-center gap-2 mb-2">
                                    <Cpu className="w-5 h-5 text-purple-400" />
                                    <h3 className="text-lg font-bold text-white">AI Prototype Roadmap</h3>
                                </div>

                                {prototypeData?.implementation_plan ? (
                                    <div className="space-y-4">
                                        {prototypeData.implementation_plan.split('\n').filter((l: string) => l.trim()).map((step: string, i: number) => (
                                            <div key={i} className="group flex gap-4 p-5 bg-white/[0.03] border border-white/5 rounded-2xl hover:border-white/10 transition-all duration-300">
                                                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm font-bold text-white/40 group-hover:text-cyan-400 transition-colors">
                                                    {i + 1}
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-sm font-bold text-white group-hover:text-cyan-400 transition-colors">
                                                        {step.split(':')[0].replace(/^[0-9\.\s]+/, '')}
                                                    </p>
                                                    <p className="text-xs text-white/50 leading-relaxed">
                                                        {step.split(':').slice(1).join(':').trim()}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="p-8 border border-white/5 border-dashed rounded-2xl text-center">
                                        <p className="text-sm text-white/20">Click Launch Prototype to generate roadmap</p>
                                    </div>
                                )}

                                <div className="flex items-center gap-3 p-4 bg-white/[0.02] border border-white/5 rounded-2xl">
                                    <CheckCircle2 className="w-5 h-5 text-green-500/50" />
                                    <p className="text-[10px] text-white/30 leading-tight">
                                        This roadmap is generated by SolveStack AI (Groq · Llama 3 70B) and is optimized for MVP development based on engineering impact signals.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-white/5 bg-black/20 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-8 py-2.5 bg-white text-black font-bold text-sm rounded-xl hover:bg-white/90 transition-all shadow-lg"
                    >
                        Acknowledge Intelligence
                    </button>
                </div>
            </div>
        </div>
    );
};

export default InferenceOverlay;
