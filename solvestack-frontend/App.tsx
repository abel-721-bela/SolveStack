
import React from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Welcome from './pages/Welcome';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import ProblemDetail from './pages/ProblemDetail';
import Profile from './pages/Profile';
import Auth from './pages/Auth';
import Interests from './pages/Interests';
import Trending from './pages/Trending';
import Squads from './pages/Squads';
import SquadChat from './pages/SquadChat';

import { AuthProvider } from './contexts/AuthContext';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Welcome />} />
          <Route path="/landing" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/trending" element={<Trending />} />
          <Route path="/interests" element={<Interests />} />
          <Route path="/squads" element={<Squads />} />
          <Route path="/squads/:id/chat" element={<SquadChat />} />
          <Route path="/problem/:id" element={<ProblemDetail />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/login" element={<Auth />} />
          <Route path="/register" element={<Auth />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
