const AI_API_URL = 'http://localhost:8002/ai';

export const postQuery = async (question, token) => {
    const response = await fetch(`${AI_API_URL}/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ question }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get response from AI.');
    return data;
};

export const getDashboardData = async (token) => {
    const response = await fetch(`${AI_API_URL}/dashboard`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get dashboard data.');
    return data;
};

export const getUserDevices = async (token) => {
    const response = await fetch(`${AI_API_URL}/devices`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to get devices.');
    return data;
};