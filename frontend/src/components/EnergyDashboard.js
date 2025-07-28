import React from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ConsumptionTimeline } from './ConsumptionTimeline';

export const EnergyDashboard = ({ data, onRefresh }) => {
    if (!data) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-gray-400">Loading dashboard data...</div>
            </div>
        );
    }

    const COLORS = ['#6366F1', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#3B82F6'];

    const roomData = data.current_usage.reduce((acc, device) => {
        if (!acc[device.room]) acc[device.room] = 0;
        acc[device.room] += device.usage;
        return acc;
    }, {});

    const pieData = Object.entries(roomData).map(([room, usage]) => ({
        name: room.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: parseFloat(usage.toFixed(2))
    }));

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                    <h3 className="text-sm font-medium text-gray-400">Current Usage</h3>
                    <p className="mt-2 text-3xl font-bold text-indigo-400">
                        {data.current_usage.reduce((sum, d) => sum + d.usage, 0).toFixed(2)} kW
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Real-time power consumption</p>
                </div>
                <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                    <h3 className="text-sm font-medium text-gray-400">Today's Total</h3>
                    <p className="mt-2 text-3xl font-bold text-green-400">
                        {data.today_total.toFixed(2)} kWh
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Since midnight</p>
                </div>
                <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                    <h3 className="text-sm font-medium text-gray-400">Monthly Cost</h3>
                    <p className="mt-2 text-3xl font-bold text-yellow-400">
                        ${data.estimated_monthly_cost.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Estimated at $0.12/kWh</p>
                </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Usage by Room */}
                <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                    <h3 className="text-lg font-semibold text-white mb-4">Usage by Room</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={pieData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                                isAnimationActive={false}
                            >
                                {pieData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip 
                                formatter={(value) => `${value.toFixed(2)} kW`}
                                contentStyle={{ backgroundColor: '#2D3748', border: '1px solid #4A5568' }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Top Devices */}
                <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                    <h3 className="text-lg font-semibold text-white mb-4">Top Energy Consumers</h3>
                    <div className="space-y-3">
                        {data.current_usage
                            .sort((a, b) => b.usage - a.usage)
                            .slice(0, 5)
                            .map((device, index) => (
                                <div key={index} className="flex items-center justify-between">
                                    <div className="flex items-center space-x-3">
                                        <div className={`w-3 h-3 rounded-full`} style={{backgroundColor: COLORS[index]}}></div>
                                        <div>
                                            <p className="text-sm font-medium text-white">{device.name}</p>
                                            <p className="text-xs text-gray-400">{device.room.replace('_', ' ')}</p>
                                        </div>
                                    </div>
                                    <p className="text-sm font-semibold text-gray-300">{device.usage.toFixed(2)} kW</p>
                                </div>
                            ))}
                    </div>
                </div>
            </div>

            {/* Devices List */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-white">All Devices</h3>
                    <button
                        onClick={onRefresh}
                        className="text-sm text-indigo-400 hover:text-indigo-300"
                    >
                        Refresh
                    </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {data.current_usage.map((device, index) => (
                        <div key={index} className={`rounded-lg p-4 border ${
                            device.usage === 0 
                                ? 'bg-gray-800 border-gray-700 opacity-60' 
                                : 'bg-gray-700 border-gray-600'
                        }`}>
                            <div className="flex items-start justify-between">
                                <div>
                                    <h4 className="font-medium text-white">{device.name}</h4>
                                    <p className="text-xs text-gray-400 mt-1">{device.type} • {device.room.replace('_', ' ')}</p>
                                </div>
                                <div className="text-right">
                                    <p className={`text-lg font-semibold ${
                                        device.usage === 0 ? 'text-gray-500' : 'text-indigo-400'
                                    }`}>
                                        {device.usage.toFixed(2)}
                                    </p>
                                    <p className="text-xs text-gray-400">kW</p>
                                    {device.usage === 0 && (
                                        <p className="text-xs text-gray-500 mt-1">Inactive</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Consumption Timeline */}
            <ConsumptionTimeline />
        </div>
    );
};
