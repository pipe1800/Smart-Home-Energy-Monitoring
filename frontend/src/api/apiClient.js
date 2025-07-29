const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

export const apiClient = async (url, options = {}, retries = 0) => {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        return response.json();
    } catch (error) {
        if (retries < MAX_RETRIES && error.message.includes('Network')) {
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
            return apiClient(url, options, retries + 1);
        }
        throw error;
    }
};

// Base API configuration
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost';

export const getAuthHeaders = (token) => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
});

export const endpoints = {
    auth: `${API_BASE_URL}:8000/auth`,
    telemetry: `${API_BASE_URL}:8001`,
    ai: `${API_BASE_URL}:8002/ai`,
    device: `${API_BASE_URL}:8003`
};
