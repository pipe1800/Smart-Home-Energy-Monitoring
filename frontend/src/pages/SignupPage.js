import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { AuthForm } from '../components/AuthForm';

export const SignupPage = ({ onSwitch }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const auth = useAuth();

    const handleSignup = async (email, password) => {
        setIsLoading(true);
        setError('');
        setMessage('');
        try {
            await auth.signup(email, password);
            setMessage('Registration successful! Please sign in.');
            setTimeout(() => onSwitch(), 2000); // Switch to login after a delay
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <h2 className="mt-6 text-center text-3xl font-extrabold text-indigo-400">Create a new account</h2>
            </div>
            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-gray-800 py-8 px-4 shadow sm:rounded-lg sm:px-10">
                    <AuthForm isLogin={false} onSubmit={handleSignup} isLoading={isLoading} error={error} />
                    {message && <p className="mt-4 text-sm text-green-400">{message}</p>}
                    <div className="mt-6">
                        <div className="relative"><div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-600" /></div><div className="relative flex justify-center text-sm"><span className="px-2 bg-gray-800 text-gray-400">Or</span></div></div>
                        <div className="mt-6">
                            <button onClick={onSwitch} className="w-full inline-flex justify-center py-2 px-4 border border-gray-600 rounded-md shadow-sm bg-gray-700 text-sm font-medium text-white hover:bg-gray-600">
                                Sign in instead
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};