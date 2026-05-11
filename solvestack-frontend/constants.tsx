
import React from 'react';
import {
  Code2,
  Terminal,
  Cpu,
  Globe,
  Zap,
  Search,
  MessageSquare,
  Heart,
  Users,
  Share2,
  TrendingUp,
  Layout
} from 'lucide-react';

export const THEME_COLOR = '#00ffcc'; // Grok/Cyberpunk Cyan

export const PLATFORM_ICONS = {
  'Stack Overflow': <Code2 className="w-4 h-4 text-orange-400" />,
  'Hacker News': <Globe className="w-4 h-4 text-orange-600" />,
  'GitHub': <Terminal className="w-4 h-4 text-purple-500" />
};

export const DIFFICULTY_COLORS = {
  Beginner: 'bg-green-500/10 text-green-500 border-green-500/20',
  Intermediate: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  Advanced: 'bg-red-500/10 text-red-500 border-red-500/20'
};
