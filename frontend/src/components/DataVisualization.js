import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export const DataVisualization = ({ data }) => {
    if (!data || (!data.data && !data.value)) {
        return <p className="text-gray-400">Sorry, I couldn't process that request.</p>;
    }
    
    if (data.data && data.data.length === 0) {
        return <p className="text-gray-400">No data available to display for your query.</p>;
    }

    if (data.data && data.data[0]?.timestamp) {
        const chartData = data.data.map(d => ({
            time: new Date(d.timestamp).toLocaleTimeString(),
            usage: d.usage
        }));
        return (
            <div className="mt-4 p-4 bg-gray-800 rounded-lg">
                <h3 className="text-lg font-semibold text-white mb-4">{data.summary}</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
                        <XAxis dataKey="time" stroke="#A0AEC0" />
                        <YAxis stroke="#A0AEC0" />
                        <Tooltip contentStyle={{ backgroundColor: '#2D3748', border: '1px solid #4A5568' }} cursor={{fill: 'rgba(128, 128, 128, 0.2)'}}/>
                        <Legend />
                        <Bar dataKey="usage" fill="#667EEA" />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        );
    }

    if (data.data && data.data[0]?.name) {
        return (
            <div className="mt-4">
                <h3 className="text-lg font-semibold text-white mb-2">{data.summary}</h3>
                <ul className="space-y-2">
                    {data.data.map(device => (
                        <li key={device.id} className="bg-gray-800 p-3 rounded-md text-gray-300">
                            {device.name}
                        </li>
                    ))}
                </ul>
            </div>
        );
    }
    
    if (data.hasOwnProperty('value') && data.value !== null) {
         return (
            <div className="mt-4 text-center">
                <h3 className="text-lg font-semibold text-white mb-2">{data.summary}</h3>
                <p className="text-4xl font-bold text-indigo-400">{Number(data.value).toFixed(2)}</p>
            </div>
        );
    }

    return <p className="text-gray-400">I received a response, but I'm not sure how to display it.</p>;
};