
export enum Difficulty {
  BEGINNER = 'Beginner',
  INTERMEDIATE = 'Intermediate',
  ADVANCED = 'Advanced'
}

export enum Source {
  REDDIT = 'Reddit',
  STACKOVERFLOW = 'Stack Overflow',
  HACKERNEWS = 'Hacker News',
  GITHUB = 'GitHub'
}

export enum SolutionType {
  SOFTWARE = 'Software',
  HARDWARE = 'Hardware',
  HYBRID = 'Hybrid'
}

export interface Problem {
  id: string;
  title: string;
  description: string;
  humanExplanation: string;
  techStack: string[];
  difficulty: Difficulty;
  estimatedEffort: string;
  source: Source;
  sourceUrl: string;
  solutionType: SolutionType;
  interestedCount: number;
  isInterested?: boolean;
  collaboratorsCount: number;
  createdAt: string;
  engineeringImpactScore?: number;
  technicalDepthScore?: number;
  industryImpactScore?: number;
  cognitiveComplexityScore?: number;
  signalQualityScore?: number;
  isNew?: boolean;
  squadStatus?: 'pending' | 'accepted' | 'rejected' | 'none';
}

export interface User {
  id: string;
  username: string;
  email: string;
  skills: string[];
  interests: string[];
  experienceLevel: string;
  activityScore: number;
  interestedCount: number;
  squadsCount: number;
  isPremium: boolean;
  createdAt: string;
}

export interface AnalyticsData {
  platform: string;
  count: number;
}

export interface TechStackData {
  name: string;
  value: number;
}
