import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { getUserDevices } from '../api/aiService';
import { createDevice, updateDevice, deleteDevice, setDeviceSchedule, getDeviceSchedule } from '../api/deviceService';

export const DeviceManager = ({ onClose, onDeviceChange }) => {
    const [devices, setDevices] = useState([]);
    const [selectedDevice, setSelectedDevice] = useState(null);
    const [schedule, setSchedule] = useState([]);
    const [showAddDevice, setShowAddDevice] = useState(false);
    const [newDevice, setNewDevice] = useState({ 
        name: '', 
        type: 'appliance', 
        room: 'living_room',
        customType: '',
        customRoom: ''
    });
    const auth = useAuth();

    const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const deviceTypes = ['appliance', 'light', 'thermostat', 'outlet', 'ev_charger', 'pool_pump', 'hvac', 'custom'];
    const rooms = ['living_room', 'kitchen', 'bedroom', 'bathroom', 'office', 'laundry', 'garage', 'basement', 'outdoor', 'custom'];
    
    useEffect(() => {
        loadDevices();
    }, []);

    const loadDevices = async () => {
        try {
            const data = await getUserDevices(auth.token);
            setDevices(data.devices);
        } catch (error) {
            console.error('Failed to load devices:', error);
        }
    };

    const handleDeviceSelect = async (device) => {
        setSelectedDevice(device);
        try {
            const scheduleData = await getDeviceSchedule(device.id, auth.token);
            setSchedule(scheduleData.schedule || []);
        } catch (error) {
            setSchedule([]);
        }
    };

    const handleCreateDevice = async () => {
        const deviceData = {
            name: newDevice.name,
            type: newDevice.type === 'custom' ? newDevice.customType : newDevice.type,
            room: newDevice.room === 'custom' ? newDevice.customRoom : newDevice.room,
            power_rating: 1.0  // Default value, will be overridden by schedule
        };
        
        try {
            await createDevice(deviceData, auth.token);
            await loadDevices();
            setShowAddDevice(false);
            setNewDevice({ name: '', type: 'appliance', room: 'living_room', customType: '', customRoom: '' });
            onDeviceChange?.(); // Trigger dashboard refresh
        } catch (error) {
            alert('Failed to create device');
        }
    };

    const handleDeleteDevice = async () => {
        if (!selectedDevice || !window.confirm('Delete this device?')) return;
        
        try {
            await deleteDevice(selectedDevice.id, auth.token);
            setSelectedDevice(null);
            await loadDevices();
            onDeviceChange?.(); // Trigger dashboard refresh
        } catch (error) {
            alert('Failed to delete device');
        }
    };

    const addScheduleBlock = (dayOfWeek) => {
        setSchedule([...schedule, {
            day_of_week: dayOfWeek,
            start_hour: 9,
            end_hour: 17,
            power_consumption: selectedDevice?.power_rating || 1.0
        }]);
    };

    const updateScheduleBlock = (index, field, value) => {
        const newSchedule = [...schedule];
        newSchedule[index][field] = Number(value);
        setSchedule(newSchedule);
    };

    const removeScheduleBlock = (index) => {
        setSchedule(schedule.filter((_, i) => i !== index));
    };

    const saveSchedule = async () => {
        try {
            await setDeviceSchedule(selectedDevice.id, schedule, auth.token);
            alert('Schedule saved successfully!');
        } catch (error) {
            alert('Failed to save schedule');
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-6xl max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-bold text-white">Device Management</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Device List */}
                    <div className="col-span-1">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold text-white">Your Devices</h3>
                            <button
                                onClick={() => setShowAddDevice(true)}
                                className="text-sm bg-indigo-600 text-white px-3 py-1 rounded hover:bg-indigo-700"
                            >
                                + Add Device
                            </button>
                        </div>
                        
                        <div className="space-y-2 mb-4">
                            {devices.map(device => (
                                <button
                                    key={device.id}
                                    onClick={() => handleDeviceSelect(device)}
                                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                                        selectedDevice?.id === device.id 
                                            ? 'bg-indigo-600 text-white' 
                                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                    }`}
                                >
                                    <div className="font-medium">{device.name}</div>
                                    <div className="text-sm opacity-75">{device.room.replace('_', ' ')}</div>
                                    <div className="text-xs opacity-60">{device.type}</div>
                                </button>
                            ))}
                        </div>

                        {selectedDevice && (
                            <button
                                onClick={handleDeleteDevice}
                                className="w-full bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700"
                            >
                                Delete Selected Device
                            </button>
                        )}
                    </div>

                    {/* Add Device Form */}
                    {showAddDevice && (
                        <div className="col-span-2 bg-gray-700 rounded-lg p-4">
                            <h3 className="text-lg font-semibold text-white mb-4">Add New Device</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm text-gray-300 mb-1">Device Name</label>
                                    <input
                                        type="text"
                                        value={newDevice.name}
                                        onChange={(e) => setNewDevice({...newDevice, name: e.target.value})}
                                        className="w-full bg-gray-800 text-white rounded px-3 py-2"
                                        placeholder="e.g., Living Room TV"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-300 mb-1">Type</label>
                                    <select
                                        value={newDevice.type}
                                        onChange={(e) => setNewDevice({...newDevice, type: e.target.value})}
                                        className="w-full bg-gray-800 text-white rounded px-3 py-2"
                                    >
                                        {deviceTypes.map(type => (
                                            <option key={type} value={type}>{type === 'custom' ? 'Other...' : type.replace('_', ' ')}</option>
                                        ))}
                                    </select>
                                    {newDevice.type === 'custom' && (
                                        <input
                                            type="text"
                                            value={newDevice.customType}
                                            onChange={(e) => setNewDevice({...newDevice, customType: e.target.value})}
                                            className="w-full bg-gray-800 text-white rounded px-3 py-2 mt-2"
                                            placeholder="Enter custom type"
                                        />
                                    )}
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-300 mb-1">Room</label>
                                    <select
                                        value={newDevice.room}
                                        onChange={(e) => setNewDevice({...newDevice, room: e.target.value})}
                                        className="w-full bg-gray-800 text-white rounded px-3 py-2"
                                    >
                                        {rooms.map(room => (
                                            <option key={room} value={room}>{room === 'custom' ? 'Other...' : room.replace('_', ' ')}</option>
                                        ))}
                                    </select>
                                    {newDevice.room === 'custom' && (
                                        <input
                                            type="text"
                                            value={newDevice.customRoom}
                                            onChange={(e) => setNewDevice({...newDevice, customRoom: e.target.value})}
                                            className="w-full bg-gray-800 text-white rounded px-3 py-2 mt-2"
                                            placeholder="Enter custom room"
                                        />
                                    )}
                                </div>
                            </div>
                            <div className="flex gap-2 mt-4">
                                <button
                                    onClick={handleCreateDevice}
                                    className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                                >
                                    Create Device
                                </button>
                                <button
                                    onClick={() => setShowAddDevice(false)}
                                    className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-500"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Schedule Editor */}
                    {selectedDevice && !showAddDevice && (
                        <div className="col-span-2">
                            <h3 className="text-lg font-semibold text-white mb-4">
                                Schedule for {selectedDevice.name}
                            </h3>
                            <div className="bg-gray-700 rounded-lg p-4">
                                <div className="mb-4">
                                    <p className="text-sm text-gray-400 mb-2">
                                        Define when this device typically runs and its power consumption (in kW).
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        Power = actual draw in kW (e.g., 1.5kW heater for 2 hours = 3kWh total)
                                    </p>
                                </div>

                                {daysOfWeek.map((day, dayIndex) => {
                                    const daySchedules = schedule.filter(s => s.day_of_week === dayIndex);
                                    return (
                                        <div key={dayIndex} className="mb-4 pb-3 border-b border-gray-600 last:border-b-0">
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="text-sm font-medium text-gray-300">{day}</h4>
                                                <button
                                                    onClick={() => addScheduleBlock(dayIndex)}
                                                    className="text-xs text-indigo-400 hover:text-indigo-300"
                                                >
                                                    + Add time block
                                                </button>
                                            </div>
                                            {daySchedules.length === 0 ? (
                                                <p className="text-xs text-gray-500 italic">No usage scheduled</p>
                                            ) : (
                                                <div className="space-y-2">
                                                    {schedule.map((block, index) => {
                                                        if (block.day_of_week !== dayIndex) return null;
                                                        return (
                                                            <div key={index} className="flex items-center gap-2 bg-gray-800 p-2 rounded">
                                                                <span className="text-xs text-gray-400 w-8">From</span>
                                                                <input
                                                                    type="number"
                                                                    min="0"
                                                                    max="23"
                                                                    value={block.start_hour}
                                                                    onChange={(e) => updateScheduleBlock(index, 'start_hour', e.target.value)}
                                                                    className="w-16 bg-gray-700 text-white rounded px-2 py-1 text-sm"
                                                                />
                                                                <span className="text-xs text-gray-400">to</span>
                                                                <input
                                                                    type="number"
                                                                    min="0"
                                                                    max="23"
                                                                    value={block.end_hour}
                                                                    onChange={(e) => updateScheduleBlock(index, 'end_hour', e.target.value)}
                                                                    className="w-16 bg-gray-700 text-white rounded px-2 py-1 text-sm"
                                                                />
                                                                <span className="text-xs text-gray-400">at</span>
                                                                <input
                                                                    type="number"
                                                                    min="0"
                                                                    step="0.1"
                                                                    value={block.power_consumption}
                                                                    onChange={(e) => updateScheduleBlock(index, 'power_consumption', e.target.value)}
                                                                    className="w-20 bg-gray-700 text-white rounded px-2 py-1 text-sm"
                                                                />
                                                                <span className="text-gray-400 text-xs">kW</span>
                                                                <button
                                                                    onClick={() => removeScheduleBlock(index)}
                                                                    className="text-red-400 hover:text-red-300 ml-auto"
                                                                >
                                                                    ×
                                                                </button>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}

                                <div className="flex gap-2 mt-6">
                                    <button
                                        onClick={saveSchedule}
                                        className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
                                    >
                                        Save Schedule
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
