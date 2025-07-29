import React from 'react';

export const ChatMessage = ({ message }) => {
    const { role, content } = message;
    const isUser = role === 'user';
    const isError = role === 'error';

    if (isError) {
        return (
            <div className="flex justify-center my-2">
                <div className="bg-red-900 bg-opacity-50 text-red-200 p-2 rounded-lg w-full text-sm">
                    <p className="font-bold">Error</p>
                    <p>{content}</p>
                </div>
            </div>
        );
    }
    
    if (role === 'system') {
        return (
             <div className="flex justify-center my-2">
                <div className="bg-gray-700 bg-opacity-50 text-gray-300 p-2 rounded-lg w-full text-center text-sm">
                    <p>{content}</p>
                </div>
            </div>
        )
    }

    // For assistant messages with data visualizations, use full width
    const isDataVisualization = !isUser && typeof content !== 'string';
    
    return (
        <div className={`flex my-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`p-3 rounded-2xl text-sm ${
                isUser 
                    ? 'bg-indigo-700 text-white rounded-br-none max-w-[80%]' 
                    : isDataVisualization
                        ? 'bg-gray-700 text-gray-200 rounded-bl-none w-full'
                        : 'bg-gray-700 text-gray-200 rounded-bl-none max-w-[80%]'
            }`}>
                {typeof content === 'string' ? <p>{content}</p> : content}
            </div>
        </div>
    );
};