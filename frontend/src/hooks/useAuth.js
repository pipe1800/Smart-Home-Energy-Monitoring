import { useState, useEffect, createContext, useContext } from 'react';
import { loginUser, registerUser } from '../api/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const storedToken = localStorage.getItem('authToken');
        if (storedToken) {
            setToken(storedToken);
        }
        setIsLoading(false);
    }, []);

    const login = async (email, password) => {
        const data = await loginUser(email, password);
        setToken(data.access_token);
        localStorage.setItem('authToken', data.access_token);
        return data;
    };

    const signup = async (email, password) => {
        return await registerUser(email, password);
    };

    const logout = () => {
        setToken(null);
        localStorage.removeItem('authToken');
    };

    const value = { token, isLoading, login, signup, logout };

    return <AuthContext.Provider value={value}>{!isLoading && children}</AuthContext.Provider>;
};

export const useAuth = () => {
    return useContext(AuthContext);
};