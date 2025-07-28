import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import { postQuery } from '../api/aiService';
import { ChatMessage } from '../components/ChatMessage';
import { DataVisualization } from '../components/DataVisualization';

export const DashboardPage = () => {
    const [messages, setMessages] = useState([{role: 'system', content: 'Welcome! How can I help you analyze your energy data?'}]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const chatEndRef = useRef(null);
    const auth = useAuth();

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        const currentInput = input;
        setInput('');
        setIsLoading(true);

        try {
            const data = await postQuery(currentInput, auth.token);
            const aiMessage = { role: 'assistant', content: <DataVisualization data={data} /> };
            setMessages(prev => [...prev, aiMessage]);
        } catch (err) {
            const errorMessage = { role: 'error', content: err.message };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gray-900 text-white">
            <header className="flex justify-between items-center p-4 bg-gray-800 border-b border-gray-700 shadow-md">
                <h1 className="text-xl font-bold text-indigo-400">Smart Home AI</h1>
                <button onClick={auth.logout} className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                    Logout
                </button>
            </header>
            <main className="flex-1 overflow-y-auto p-4 md:p-6">
                <div className="max-w-4xl mx-auto">
                    {messages.map((msg, index) => (<ChatMessage key={index} message={msg} />))}
                    {isLoading && <ChatMessage message={{role: 'assistant', content: 'Thinking...'}} />}
                    <div ref={chatEndRef} />
                </div>
            </main>
            <footer className="p-4 bg-gray-800 border-t border-gray-700">
                <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto flex items-center space-x-2">
                    <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="e.g., What was the total usage for my Living Room AC yesterday?" className="flex-1 bg-gray-700 border border-gray-600 rounded-lg p-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500" disabled={isLoading} />
                    <button type="submit" disabled={isLoading || !input.trim()} className="bg-indigo-600 text-white rounded-lg p-3 disabled:bg-indigo-400 disabled:cursor-not-allowed hover:bg-indigo-700 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
                    </button>
                </form>
            </footer>
        </div>
    );
};