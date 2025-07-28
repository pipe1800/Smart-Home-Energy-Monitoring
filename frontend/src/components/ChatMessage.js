import React from 'react';

export const ChatMessage = ({ message }) => {
    const { role, content } = message;
    const isUser = role === 'user';
    const isError = role === 'error';

    if (isError) {
        return (
            <div className="flex justify-center my-2">
                <div className="bg-red-900 bg-opacity-50 text-red-200 p-3 rounded-lg max-w-2xl w-full">
                    <p className="font-bold">Error</p>
                    <p>{content}</p>
                </div>
            </div>
        );
    }
    
    if (role === 'system') {
        return (
             <div className="flex justify-center my-2">
                <div className="bg-gray-700 bg-opacity-50 text-gray-300 p-3 rounded-lg max-w-2xl w-full text-center">
                    <p>{content}</p>
                </div>
            </div>
        )
    }

    return (
        <div className={`flex my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`p-4 rounded-2xl max-w-3xl ${isUser ? 'bg-indigo-700 text-white rounded-br-none' : 'bg-gray-700 text-gray-200 rounded-bl-none'}`}>
                {typeof content === 'string' ? <p>{content}</p> : content}
            </div>
        </div>
    );
};