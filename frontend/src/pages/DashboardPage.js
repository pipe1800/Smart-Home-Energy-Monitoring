import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import { postQuery, getDashboardData } from '../api/aiService';
import { ChatMessage } from '../components/ChatMessage';
import { DataVisualization } from '../components/DataVisualization';
import { EnergyDashboard } from '../components/EnergyDashboard';
import { DeviceManager } from '../components/DeviceManager';

export const DashboardPage = () => {
    const [messages, setMessages] = useState([{role: 'system', content: 'Welcome! How can I help you analyze your energy data?'}]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showChat, setShowChat] = useState(false);
    const [showDeviceManager, setShowDeviceManager] = useState(false);
    const [dashboardData, setDashboardData] = useState(null);
    const chatEndRef = useRef(null);
    const auth = useAuth();

    useEffect(() => {
        loadDashboardData();
        const interval = setInterval(loadDashboardData, 30000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadDashboardData = async () => {
        try {
            const data = await getDashboardData(auth.token);
            setDashboardData(prevData => {
                if (JSON.stringify(prevData) !== JSON.stringify(data)) {
                    return data;
                }
                return prevData;
            });
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    };

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
                <h1 className="text-xl font-bold text-indigo-400">Smart Home Energy Monitor</h1>
                <div className="flex items-center gap-2">
                    <button 
                        onClick={() => setShowDeviceManager(true)}
                        className="py-2 px-4 border border-gray-600 rounded-md shadow-sm text-sm font-medium text-white bg-gray-700 hover:bg-gray-600"
                    >
                        Manage Devices
                    </button>
                    <button onClick={auth.logout} className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                        Logout
                    </button>
                </div>
            </header>
            
            <main className="flex-1 overflow-y-auto p-4 md:p-6">
                <EnergyDashboard data={dashboardData} onRefresh={loadDashboardData} />
            </main>

            {!showChat && (
                <button
                    onClick={() => setShowChat(true)}
                    className="fixed bottom-6 right-6 bg-indigo-600 text-white rounded-full p-4 shadow-lg hover:bg-indigo-700 transition-all duration-200 hover:scale-110 z-50"
                    aria-label="Open AI Assistant"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                </button>
            )}

            {showChat && (
                <div className="fixed bottom-6 right-6 w-[500px] h-[600px] bg-gray-800 rounded-lg shadow-2xl flex flex-col z-50 border border-gray-700">
                    <div className="flex justify-between items-center p-4 border-b border-gray-700">
                        <h3 className="text-lg font-semibold text-indigo-400">AI Assistant</h3>
                        <button
                            onClick={() => setShowChat(false)}
                            className="text-gray-400 hover:text-white transition-colors"
                            aria-label="Close chat"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    
                    <div className="flex-1 overflow-y-auto p-4">
                        {messages.map((msg, index) => (<ChatMessage key={index} message={msg} />))}
                        {isLoading && <ChatMessage message={{role: 'assistant', content: 'Thinking...'}} />}
                        <div ref={chatEndRef} />
                    </div>
                    
                    <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-700">
                        <div className="flex items-center space-x-2">
                            <input 
                                type="text" 
                                value={input} 
                                onChange={(e) => setInput(e.target.value)} 
                                placeholder="Ask about your energy usage..." 
                                className="flex-1 bg-gray-700 border border-gray-600 rounded-lg p-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm" 
                                disabled={isLoading} 
                            />
                            <button 
                                type="submit" 
                                disabled={isLoading || !input.trim()} 
                                className="bg-indigo-600 text-white rounded-lg p-2 disabled:bg-indigo-400 disabled:cursor-not-allowed hover:bg-indigo-700 transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                </svg>
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {showDeviceManager && (
                <DeviceManager 
                    onClose={() => setShowDeviceManager(false)} 
                    onDeviceChange={loadDashboardData}
                />
            )}
        </div>
    );
};