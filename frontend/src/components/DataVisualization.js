import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export const DataVisualization = ({ data }) => {
    if (!data) {
        return <p className="text-gray-400">Sorry, I couldn't process that request.</p>;
    }
    
    if (data.content && !data.data && !data.value) {
        return (
            <div className="mt-2 p-4 bg-gray-800 rounded-lg">
                <h3 className="text-base font-semibold text-indigo-400 mb-2">{data.summary || 'Response'}</h3>
                <div className="text-sm text-gray-300 whitespace-pre-wrap">{data.content}</div>
            </div>
        );
    }
    
    if (data.data && data.data.length === 0) {
        return (
            <div className="mt-2 text-gray-400">
                {data.content || "No data available to display for your query."}
            </div>
        );
    }

    if (data.data && data.data[0]?.timestamp) {
        const chartData = data.data.map(d => ({
            time: new Date(d.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
            usage: d.usage
        })).reverse();
        
        return (
            <div className="mt-4 p-4 bg-gray-800 rounded-lg">
                <h3 className="text-lg font-semibold text-white mb-2">{data.summary}</h3>
                <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
                        <XAxis dataKey="time" stroke="#A0AEC0" fontSize={10} angle={-45} textAnchor="end" height={60} />
                        <YAxis 
                            stroke="#A0AEC0" 
                            fontSize={10}
                            domain={[0, 5]}
                            ticks={[0, 1, 2, 3, 4, 5]}
                            tickFormatter={(value) => `${value} kWh`}
                            allowDataOverflow={false}
                            scale="linear"
                        />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#2D3748', border: '1px solid #4A5568' }} 
                            cursor={{fill: 'rgba(128, 128, 128, 0.2)'}}
                            formatter={(value) => `${value.toFixed(2)} kWh`}
                        />
                        <Bar dataKey="usage" fill="#667EEA" />
                    </BarChart>
                </ResponsiveContainer>
                {(data.daily_total || data.daily_cost) && (
                    <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                        {data.daily_total && (
                            <div className="bg-gray-700 p-2 rounded">
                                <span className="text-gray-400">24h Total:</span>
                                <span className="text-white font-semibold ml-2">{data.daily_total}</span>
                            </div>
                        )}
                        {data.daily_cost && (
                            <div className="bg-gray-700 p-2 rounded">
                                <span className="text-gray-400">24h Cost:</span>
                                <span className="text-green-400 font-semibold ml-2">{data.daily_cost}</span>
                            </div>
                        )}
                    </div>
                )}
                {data.additional_info && (
                    <p className="text-xs text-gray-400 mt-2">{data.additional_info}</p>
                )}
            </div>
        );
    }

    if (data.data && data.data[0]?.name) {
        return (
            <div className="mt-4">
                <h3 className="text-lg font-semibold text-white mb-2">{data.summary}</h3>
                <div className="grid grid-cols-1 gap-2">
                    {data.data.map(device => (
                        <div key={device.id} className="bg-gray-800 p-3 rounded-md flex items-center justify-between">
                            <div>
                                <span className="text-gray-300 font-medium">{device.name}</span>
                                <span className="text-gray-500 text-xs ml-2">({device.type})</span>
                            </div>
                            <span className="text-gray-400 text-sm">{device.room.replace('_', ' ')}</span>
                        </div>
                    ))}
                </div>
            </div>
        );
    }
    
    if (data.hasOwnProperty('value') && data.value !== null) {
        return (
            <div className="mt-4 p-4 bg-gray-800 rounded-lg">
                <h3 className="text-lg font-semibold text-white mb-2">{data.summary}</h3>
                <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                        <p className="text-3xl font-bold text-indigo-400">
                            {Number(data.value).toFixed(2)}
                            {data.unit && <span className="text-xl ml-1 text-gray-400">{data.unit}</span>}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">Actual Usage</p>
                    </div>
                    {data.cost && (
                        <div className="text-center">
                            <p className="text-3xl font-bold text-green-400">{data.cost}</p>
                            <p className="text-xs text-gray-500 mt-1">Actual Cost</p>
                        </div>
                    )}
                </div>
                {data.monthly_projection && (
                    <div className="mt-3 pt-3 border-t border-gray-700">
                        <p className="text-sm text-gray-400">
                            Monthly Projection: <span className="text-yellow-400 font-semibold">{data.monthly_projection}</span>
                            <span className="text-xs ml-2">(based on usage schedule)</span>
                        </p>
                    </div>
                )}
                {data.additional_info && (
                    <p className="text-xs text-gray-400 mt-2">{data.additional_info}</p>
                )}
            </div>
        );
    }

    return <p className="text-gray-400">I received a response, but I'm not sure how to display it.</p>;
};