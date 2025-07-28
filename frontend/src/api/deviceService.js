const API_URL = 'http://localhost:8001';

export const createDevice = async (device, token) => {
    const response = await fetch(`${API_URL}/devices`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(device),
    });
    if (!response.ok) throw new Error('Failed to create device');
    return response.json();
};

export const updateDevice = async (deviceId, updates, token) => {
    const response = await fetch(`${API_URL}/devices/${deviceId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updates),
    });
    if (!response.ok) throw new Error('Failed to update device');
    return response.json();
};

export const deleteDevice = async (deviceId, token) => {
    const response = await fetch(`${API_URL}/devices/${deviceId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`
        },
    });
    if (!response.ok) throw new Error('Failed to delete device');
    return response.json();
};

export const setDeviceSchedule = async (deviceId, schedule, token) => {
    const response = await fetch(`${API_URL}/devices/${deviceId}/schedule`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(schedule),
    });
    if (!response.ok) throw new Error('Failed to update schedule');
    return response.json();
};

export const getDeviceSchedule = async (deviceId, token) => {
    const response = await fetch(`${API_URL}/devices/${deviceId}/schedule`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        },
    });
    if (!response.ok) throw new Error('Failed to get schedule');
    return response.json();
};
