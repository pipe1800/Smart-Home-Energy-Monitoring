import { apiClient, endpoints, getAuthHeaders } from './apiClient';

export const createDevice = async (device, token) => {
    return apiClient(`${endpoints.telemetry}/devices`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify(device),
    });
};

export const updateDevice = async (deviceId, updates, token) => {
    return apiClient(`${endpoints.telemetry}/devices/${deviceId}`, {
        method: 'PUT',
        headers: getAuthHeaders(token),
        body: JSON.stringify(updates),
    });
};

export const deleteDevice = async (deviceId, token) => {
    return apiClient(`${endpoints.telemetry}/devices/${deviceId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(token),
    });
};

export const setDeviceSchedule = async (deviceId, schedule, token) => {
    return apiClient(`${endpoints.telemetry}/devices/${deviceId}/schedule`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify(schedule),
    });
};

export const getDeviceSchedule = async (deviceId, token) => {
    return apiClient(`${endpoints.telemetry}/devices/${deviceId}/schedule`, {
        method: 'GET',
        headers: getAuthHeaders(token),
    });
};
