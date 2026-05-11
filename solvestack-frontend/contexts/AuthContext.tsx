
import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface AuthContextType {
    user: any | null; // Replace 'any' with User type if available
    token: string | null;
    login: (token: string, user: any) => void;
    logout: () => void;
    refreshUser: () => Promise<void>;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<any | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

    useEffect(() => {
        const initAuth = async () => {
            if (token) {
                try {
                    // Fetch user info from /me
                    const userData = await apiService.getCurrentUser();
                    setUser(userData);
                } catch (error) {
                    console.error("Failed to restore auth session:", error);
                    logout();
                }
            }
        };
        initAuth();
    }, [token]);

    const login = (newToken: string, newUser: any) => {
        localStorage.setItem('token', newToken);
        setToken(newToken);
        setUser(newUser);
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    };

    const refreshUser = async () => {
        if (token) {
            try {
                const userData = await apiService.getCurrentUser();
                setUser(userData);
            } catch (error) {
                console.error("Failed to refresh user data:", error);
            }
        }
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, refreshUser, isAuthenticated: !!token }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
