
import { Problem, Difficulty, Source, SolutionType, User } from '../types';

const API_BASE_URL = 'http://localhost:8000';

// Helper to handle response errors
const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    const detail = error.detail;
    if (Array.isArray(detail)) {
      // FastAPI validation error format
      throw new Error(detail[0].msg || 'Validation error');
    }
    throw new Error(detail || 'Network response was not ok');
  }
  return response.json();
};

// Map backend problem item to Frontend Problem type
const mapItemToProblem = (item: any): Problem => ({
  id: String(item.ps_id),
  title: item.title,
  description: item.description,
  humanExplanation: item.humanized_explanation && item.humanized_explanation.trim()
    ? item.humanized_explanation
    : (item.description || '').replace(/<[^>]+>/g, '').replace(/```[\s\S]*?```/g, '').replace(/\s+/g, ' ').trim().substring(0, 200) + (item.description?.length > 200 ? '...' : ''),
  techStack: item.tags ? (Array.isArray(item.tags) ? item.tags : [item.tags]) :
    (item.suggested_tech ? (Array.isArray(item.suggested_tech) ? item.suggested_tech : item.suggested_tech.split(',').map((t: string) => t.trim())) : []),
  difficulty: (item.engineering_impact_score || 0) < 40 ? Difficulty.BEGINNER :
    (item.engineering_impact_score || 0) > 70 ? Difficulty.ADVANCED :
      Difficulty.INTERMEDIATE,
  estimatedEffort: 'Unknown',
  source: (item.source || '').includes('github') ? Source.GITHUB :
    (item.source || '').includes('hackernews') ? Source.HACKERNEWS :
      (item.source || '').includes('stackoverflow') ? Source.STACKOVERFLOW :
        (item.source || '').includes('reddit') ? Source.REDDIT :
          Source.STACKOVERFLOW,
  sourceUrl: item.reference_link || '',
  solutionType: SolutionType.SOFTWARE,
  interestedCount: item.interested_count || 0,
  isInterested: item.is_interested || false,
  collaboratorsCount: item.collaborators_count || 0,
  squadStatus: item.squad_status || 'none',
  createdAt: item.scraped_at || new Date().toISOString(),
  engineeringImpactScore: item.engineering_impact_score,
  technicalDepthScore: item.technical_depth_score,
  industryImpactScore: item.industry_impact_score,
  cognitiveComplexityScore: item.cognitive_complexity_score,
  signalQualityScore: item.signal_quality_score
});

export const apiService = {
  getProblems: async (skip: number = 0, limit: number = 100): Promise<Problem[]> => {
    const token = localStorage.getItem('token');
    try {
      const data = await fetch(`${API_BASE_URL}/problems?skip=${skip}&limit=${limit}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      }).then(handleResponse);

      return data.map(mapItemToProblem);
    } catch (error) {
      console.error("Failed to fetch problems:", error);
      return [];
    }
  },

  getProblemById: async (id: string): Promise<Problem | undefined> => {
    const token = localStorage.getItem('token');
    try {
      const item = await fetch(`${API_BASE_URL}/problems/${id}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      }).then(handleResponse);
      return mapItemToProblem(item);
    } catch (error) {
      console.error(`Failed to fetch problem ${id}:`, error);
      return undefined;
    }
  },

  login: async (email: string, password: string): Promise<{ access_token: string }> => {
    const formData = new URLSearchParams();
    formData.append('username', email); // backend expects 'username' for the OAuth2 form, even if it's an email
    formData.append('password', password);

    const data = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString()
    }).then(handleResponse);
    return data;
  },

  register: async (username: string, email: string, password: string): Promise<User> => {
    return await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, email, password })
    }).then(handleResponse);
  },

  toggleInterest: async (problemId: string): Promise<number | null> => {
    const token = localStorage.getItem('token');
    if (!token) return null;

    try {
      const data = await fetch(`${API_BASE_URL}/interest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ problem_id: parseInt(problemId) })
      }).then(handleResponse);
      return data.total_interested;
    } catch (error) {
      console.error("Failed to mark interest:", error);
      return null;
    }
  },

  removeInterest: async (problemId: string): Promise<number | null> => {
    const token = localStorage.getItem('token');
    if (!token) return null;

    try {
      const data = await fetch(`${API_BASE_URL}/interest/${problemId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }).then(handleResponse);
      return data.total_interested;
    } catch (error) {
      console.error("Failed to remove interest:", error);
      return null;
    }
  },

  getUserInterests: async (): Promise<Problem[]> => {
    const token = localStorage.getItem('token');
    if (!token) return [];

    try {
      const data = await fetch(`${API_BASE_URL}/me/interests`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }).then(handleResponse);

      return data.map(mapItemToProblem);
    } catch (error) {
      console.error("Failed to fetch user interests:", error);
      return [];
    }
  },

  getUserSquads: async (): Promise<Problem[]> => {
    const token = localStorage.getItem('token');
    if (!token) return [];

    try {
      const data = await fetch(`${API_BASE_URL}/me/squads`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }).then(handleResponse);

      return data.map(mapItemToProblem);
    } catch (error) {
      console.error("Failed to fetch user squads:", error);
      return [];
    }
  },

  requestCollaboration: async (problemId: string): Promise<boolean> => {
    const token = localStorage.getItem('token');
    if (!token) return false;

    console.log(`Requesting collaboration for problem ${problemId}`);
    try {
      await fetch(`${API_BASE_URL}/collaborate/request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ problem_id: parseInt(problemId) })
      }).then(handleResponse);
      return true;
    } catch (error) {
      console.error("Failed to request collaboration:", error);
      return false;
    }
  },

  acceptCollaboration: async (problemId: string): Promise<boolean> => {
    const token = localStorage.getItem('token');
    if (!token) return false;

    try {
      await fetch(`${API_BASE_URL}/collaborate/accept`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ problem_id: parseInt(problemId) })
      }).then(handleResponse);
      return true;
    } catch (error) {
      console.error("Failed to accept collaboration:", error);
      return false;
    }
  },

  rejectCollaboration: async (problemId: string): Promise<boolean> => {
    const token = localStorage.getItem('token');
    if (!token) return false;

    try {
      await fetch(`${API_BASE_URL}/collaborate/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ problem_id: parseInt(problemId) })
      }).then(handleResponse);
      return true;
    } catch (error) {
      console.error("Failed to reject collaboration:", error);
      return false;
    }
  },

  getCollaborationStatus: async (problemId: string): Promise<any> => {
    const token = localStorage.getItem('token');
    if (!token) return null;

    try {
      return await fetch(`${API_BASE_URL}/collaborate/${problemId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }).then(handleResponse);
    } catch (error) {
      console.error("Failed to get collaboration status:", error);
      return null;
    }
  },

  getCurrentUser: async (): Promise<User> => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('No token found');

    const data = await fetch(`${API_BASE_URL}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }).then(handleResponse);

    return {
      id: String(data.id),
      username: data.username,
      email: data.email,
      skills: data.skills || [],
      interests: data.interests || [],
      experienceLevel: data.experience_level || (data.activity_score > 50 ? 'Advanced' : data.activity_score > 10 ? 'Intermediate' : 'Beginner'),
      activityScore: data.activity_score || 0,
      interestedCount: data.interested_count || 0,
      squadsCount: data.squads_count || 0,
      isPremium: data.is_premium || false,
      createdAt: data.created_at
    };
  },

  semanticSearch: async (query: string): Promise<Problem[]> => {
    try {
      const data = await fetch(`${API_BASE_URL}/search/semantic?query=${encodeURIComponent(query)}&limit=30`)
        .then(handleResponse);

      return (data.results || []).map(mapItemToProblem);
    } catch (error) {
      console.error("Semantic search failed, trying keyword fallback:", error);
      // Fall back to keyword search
      try {
        const data = await fetch(`${API_BASE_URL}/search/keyword?query=${encodeURIComponent(query)}&limit=20`)
          .then(handleResponse);
        return (data.results || []).map(mapItemToProblem);
      } catch (e2) {
        console.error("Keyword search also failed:", e2);
        return [];
      }
    }
  },

  keywordSearch: async (query: string): Promise<Problem[]> => {
    try {
      const data = await fetch(`${API_BASE_URL}/search/keyword?query=${encodeURIComponent(query)}&limit=20`)
        .then(handleResponse);
      return (data.results || []).map(mapItemToProblem);
    } catch (error) {
      console.error("Keyword search failed:", error);
      return [];
    }
  },

  getTrendingProblems: async (): Promise<Problem[]> => {
    const token = localStorage.getItem('token');
    try {
      const data = await fetch(`${API_BASE_URL}/problems/trending`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      }).then(handleResponse);

      return data.map(mapItemToProblem);
    } catch (error) {
      console.error("Failed to fetch trending problems:", error);
      return [];
    }
  },

  scrapeProblems: async (): Promise<{ message: string; totalScraped: number; newProblems: Problem[] }> => {
    try {
      const data = await fetch(`${API_BASE_URL}/scrape/all`, {
        method: 'POST'
      }).then(handleResponse);

      return {
        message: data.message,
        totalScraped: data.total_scraped,
        newProblems: (data.new_problems || []).map(mapItemToProblem)
      };
    } catch (error) {
      console.error("Failed to trigger scraping:", error);
      throw error;
    }
  },

  async getExplanation(id: string | number) {
    try {
      const resp = await fetch(`${API_BASE_URL}/shelf/${id}/explain`);
      if (!resp.ok) return null;
      return await resp.json();
    } catch (error) {
      console.error("Failed to fetch explanation", error);
      return null;
    }
  },

  async getPrototype(id: string | number) {
    try {
      const resp = await fetch(`${API_BASE_URL}/problems/${id}/prototype`);
      if (!resp.ok) return null;
      return await resp.json();
    } catch (error) {
      console.error("Failed to generate prototype plan", error);
      return null;
    }
  },

  // ---- Squad System ----

  getSquads: async (): Promise<any[]> => {
    try {
      const data = await fetch(`${API_BASE_URL}/squads`).then(handleResponse);
      return data;
    } catch (error) {
      console.error("Failed to fetch squads:", error);
      return [];
    }
  },

  createSquad: async (problemId: number, name: string, description: string): Promise<any> => {
    const token = localStorage.getItem('token');
    return await fetch(`${API_BASE_URL}/squads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ problem_id: problemId, name, description })
    }).then(handleResponse);
  },

  joinSquad: async (squadId: number): Promise<any> => {
    const token = localStorage.getItem('token');
    return await fetch(`${API_BASE_URL}/squads/${squadId}/join`, {
      method: 'POST',
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
    }).then(handleResponse);
  },

  acceptSquadMember: async (squadId: number, userId: number): Promise<any> => {
    const token = localStorage.getItem('token');
    return await fetch(`${API_BASE_URL}/squads/${squadId}/accept/${userId}`, {
      method: 'POST',
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
    }).then(handleResponse);
  },

  rejectSquadMember: async (squadId: number, userId: number): Promise<any> => {
    const token = localStorage.getItem('token');
    return await fetch(`${API_BASE_URL}/squads/${squadId}/reject/${userId}`, {
      method: 'POST',
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
    }).then(handleResponse);
  },

  getSquadDetail: async (squadId: number): Promise<any> => {
    const token = localStorage.getItem('token');
    return await fetch(`${API_BASE_URL}/squads/${squadId}`, {
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
    }).then(handleResponse);
  },

  deleteSquad: async (squadId: number): Promise<any> => {
    const token = localStorage.getItem('token');
    return await fetch(`${API_BASE_URL}/squads/${squadId}`, {
      method: 'DELETE',
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
    }).then(handleResponse);
  },

  leaveSquad: async (squadId: number): Promise<any> => {
    const token = localStorage.getItem('token');
    return await fetch(`${API_BASE_URL}/squads/${squadId}/leave`, {
      method: 'POST',
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
    }).then(handleResponse);
  },

  getSquadMessages: async (squadId: number): Promise<any[]> => {
    const token = localStorage.getItem('token');
    try {
      const data = await fetch(`${API_BASE_URL}/squads/${squadId}/messages?limit=100`, {
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) }
      }).then(handleResponse);
      return data;
    } catch {
      return [];
    }
  }
};
