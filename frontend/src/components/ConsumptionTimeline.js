import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { getConsumptionTimeline } from '../api/aiService';
import { useAuth } from '../hooks/useAuth';

export const ConsumptionTimeline = () => {
    const [view, setView] = useState('daily');
    const [data, setData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const auth = useAuth();

    useEffect(() => {
        if (auth?.token) {
            loadTimelineData();
        }
    }, [view, auth?.token]);

    const loadTimelineData = async () => {
        if (!auth?.token) {
            console.log('No auth token available');
            return;
        }
        
        setIsLoading(true);
        try {
            const timelineData = await getConsumptionTimeline(view, auth.token);
            
            if (!timelineData || (!timelineData.historical && !timelineData.forecast)) {
                setData([]);
                return;
            }
            
            const historical = (timelineData.historical || []).map(item => ({
                ...item,
                actualUsage: item.usage,
                forecastUsage: null
            }));
            
            const forecast = (timelineData.forecast || []).map(item => ({
                ...item,
                actualUsage: null,
                forecastUsage: item.usage
            }));
            
            const combined = [...historical, ...forecast].sort((a, b) => 
                new Date(a.timestamp) - new Date(b.timestamp)
            );
            
            setData(combined);
        } catch (error) {
            console.error('Failed to load timeline data:', error);
            setData([]);
        } finally {
            setIsLoading(false);
        }
    };

    const formatXAxis = (timestamp) => {
        const date = new Date(timestamp);
        if (view === 'daily') {
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } else if (view === 'weekly') {
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } else {
            return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
        }
    };

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const actualValue = payload.find(p => p.dataKey === 'actualUsage')?.value;
            const forecastValue = payload.find(p => p.dataKey === 'forecastUsage')?.value;
            const value = actualValue || forecastValue;
            const isActual = actualValue !== null && actualValue !== undefined;
            
            if (value !== null && value !== undefined) {
                return (
                    <div className="bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-700">
                        <p className="text-sm text-gray-400">{formatXAxis(label)}</p>
                        <p className="text-lg font-semibold text-white">
                            {value.toFixed(2)} kWh
                        </p>
                        <p className="text-xs text-gray-500">
                            {isActual ? 'Actual' : 'Forecasted'}
                        </p>
                    </div>
                );
            }
        }
        return null;
    };

    if (isLoading) {
        return (
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="animate-pulse">
                    <div className="h-4 bg-gray-700 rounded w-1/4 mb-4"></div>
                    <div className="h-64 bg-gray-700 rounded"></div>
                </div>
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Consumption Timeline</h3>
                <div className="flex items-center justify-center h-64 text-gray-500">
                    <p>No consumption data available yet</p>
                </div>
            </div>
        );
    }

    const todayIndex = data?.findIndex(d => d.is_forecast) || data?.length;

    return (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-white">Consumption Timeline</h3>
                <div className="flex gap-2">
                    {['daily', 'weekly', 'monthly'].map((v) => (
                        <button
                            key={v}
                            onClick={() => setView(v)}
                            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                                view === v
                                    ? 'bg-indigo-600 text-white'
                                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            }`}
                        >
                            {v.charAt(0).toUpperCase() + v.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data || []} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                        dataKey="timestamp" 
                        tickFormatter={formatXAxis}
                        stroke="#9CA3AF"
                        fontSize={12}
                    />
                    <YAxis 
                        stroke="#9CA3AF"
                        fontSize={12}
                        tickFormatter={(value) => `${value} kWh`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend 
                        wrapperStyle={{ paddingTop: '20px' }}
                        iconType="line"
                    />
                    
                    {/* Today marker */}
                    {todayIndex > 0 && (
                        <ReferenceLine 
                            x={data?.[todayIndex - 1]?.timestamp} 
                            stroke="#6366F1" 
                            strokeDasharray="5 5"
                            label={{ value: "Today", position: "top", fill: "#6366F1" }}
                        />
                    )}
                    
                    {/* Actual consumption line */}
                    <Line
                        type="monotone"
                        dataKey="actualUsage"
                        stroke="#10B981"
                        strokeWidth={2}
                        dot={false}
                        name="Actual"
                        connectNulls={false}
                    />
                    
                    {/* Forecast line */}
                    <Line
                        type="monotone"
                        dataKey="forecastUsage"
                        stroke="#F59E0B"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        dot={false}
                        name="Forecast"
                        connectNulls={false}
                    />
                </LineChart>
            </ResponsiveContainer>

            <div className="mt-4 flex items-center justify-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                    <div className="w-4 h-0.5 bg-green-500"></div>
                    <span className="text-gray-400">Actual Consumption</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-0.5 bg-yellow-500 border-dashed"></div>
                    <span className="text-gray-400">Forecasted</span>
                </div>
            </div>
        </div>
    );
};
