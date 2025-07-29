import React, { useState } from 'react';
import { useAuth } from './hooks/useAuth';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { DashboardPage } from './pages/DashboardPage';

function App() {
    const [isLoginView, setIsLoginView] = useState(true);
    const auth = useAuth();

    if (auth.isLoading) {
        return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">Loading...</div>;
    }

    if (auth.token) {
        return <DashboardPage />;
    }

    return isLoginView
        ? <LoginPage onSwitch={() => setIsLoginView(false)} />
        : <SignupPage onSwitch={() => setIsLoginView(true)} />;
}

export default App;
