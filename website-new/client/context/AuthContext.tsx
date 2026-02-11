import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/lib/api';

interface AuthContextType {
    isLoggedIn: boolean;
    login: (accessToken: string, refreshToken: string) => void;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem('access_token'));
    const queryClient = useQueryClient();

    // Listen for storage changes from other tabs
    useEffect(() => {
        const handleStorage = (e: StorageEvent) => {
            if (e.key === 'access_token') {
                setIsLoggedIn(!!e.newValue);
            }
        };
        window.addEventListener('storage', handleStorage);
        return () => window.removeEventListener('storage', handleStorage);
    }, []);

    const login = useCallback((accessToken: string, refreshToken: string) => {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        setIsLoggedIn(true);
    }, []);

    const logout = useCallback(async () => {
        try {
            await apiService.logout();
        } catch {
            // Force logout even if API call fails
        } finally {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setIsLoggedIn(false);
            queryClient.clear();
        }
    }, [queryClient]);

    return (
        <AuthContext.Provider value={{ isLoggedIn, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
