import { apiClient, endpoints, getAuthHeaders } from './apiClient';

export const postQuery = async (question, token) => {
    return apiClient(`${endpoints.ai}/query`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({ question }),
    });
};

export const getDashboardData = async (token) => {
    return apiClient(`${endpoints.ai}/dashboard`, {
        method: 'GET',
        headers: getAuthHeaders(token),
    });
};

export const getUserDevices = async (token) => {
    return apiClient(`${endpoints.ai}/devices`, {
        method: 'GET',
        headers: getAuthHeaders(token),
    });
};

export const getConsumptionTimeline = async (view, token) => {
    return apiClient(`${endpoints.ai}/consumption-timeline?view=${view}`, {
        method: 'GET',
        headers: getAuthHeaders(token),
    });
};