import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { authAPI } from './api';

interface User {
    id: number;
    username: string;
    email: string;
    points: number;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (username: string, password: string) => Promise<void>;
    register: (username: string, email: string, password: string) => Promise<void>;
    logout: () => void;
    loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadUser = async () => {
            const storedToken = localStorage.getItem('token');
            if (storedToken) {
                try {
                    const response = await authAPI.getMeWithToken(storedToken);
                    setUser(response.data);
                } catch {
                    localStorage.removeItem('token');
                    setToken(null);
                }
            }
            setLoading(false);
        };
        loadUser();
    }, []);

    const login = async (username: string, password: string) => {
        const response = await authAPI.login(username, password);
        const newToken = response.data.access_token;
        localStorage.setItem('token', newToken);
        setToken(newToken);

        // Fetch user immediately with the new token
        const userResponse = await authAPI.getMeWithToken(newToken);
        setUser(userResponse.data);
    };

    const register = async (username: string, email: string, password: string) => {
        await authAPI.register(username, email, password);
        await login(username, password);
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};
