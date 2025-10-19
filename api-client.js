// API Client for University Activities Backend
// This file handles all communication with the Python Flask backend

// Auto-detect backend URL based on current location
function getBackendURL() {
    // Check if we're running on a custom URL (from phone/network)
    const currentHost = window.location.hostname;
    const currentPort = window.location.port;
    
    // If accessing from network (not localhost), use the same host
    if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
        return `http://${currentHost}:8080/api`;
    }
    
    // Default to localhost with correct port
    return 'http://localhost:8080/api';
}

const API_BASE_URL = getBackendURL();

// Helper function to get auth token
function getAuthToken() {
    return localStorage.getItem('authToken');
}

// Helper function to make authenticated requests
async function apiRequest(endpoint, options = {}) {
    const token = getAuthToken();
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };
    
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('الخادم غير متاح. تأكد من تشغيل Backend');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            // Handle JWT expiration
            if (response.status === 401 && data.message && data.message.includes('token')) {
                localStorage.removeItem('authToken');
                localStorage.removeItem('currentUser');
                throw new Error('انتهت صلاحية الجلسة. يرجى تسجيل الدخول مرة أخرى');
            }
            throw new Error(data.message || 'حدث خطأ في الاتصال بالخادم');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        // Check for network errors
        if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
            throw new Error('فشل الاتصال بالخادم. تأكد من أن Backend يعمل على المنفذ 8080');
        }
        throw error;
    }
}

// ==================== AUTH API ====================

async function apiRegister(userData) {
    try {
        const response = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message };
    }
}

async function apiLogin(credentials) {
    try {
        const response = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
        
        if (response.success && response.token) {
            // Store token and user info
            localStorage.setItem('authToken', response.token);
            localStorage.setItem('currentUser', JSON.stringify(response.user));
        }
        
        return response;
    } catch (error) {
        return { success: false, message: error.message };
    }
}

function apiLogout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
}

function apiGetCurrentUser() {
    const userStr = localStorage.getItem('currentUser');
    return userStr ? JSON.parse(userStr) : null;
}

// ==================== ACTIVITY API ====================

async function apiGetActivities() {
    try {
        const response = await apiRequest('/activities', {
            method: 'GET'
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message, activities: [] };
    }
}

async function apiRegisterForActivity(activityId) {
    try {
        const response = await apiRequest(`/activities/${activityId}/register`, {
            method: 'POST'
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message };
    }
}

async function apiGetMyActivityRegistrations() {
    try {
        const response = await apiRequest('/activities/my-registrations', {
            method: 'GET'
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message, registrations: [] };
    }
}

// ==================== APPLICATION API ====================

async function apiSubmitApplication(applicationData) {
    try {
        const response = await apiRequest('/applications/submit', {
            method: 'POST',
            body: JSON.stringify(applicationData)
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message };
    }
}

async function apiGetMyApplications() {
    try {
        const response = await apiRequest('/applications/my-applications', {
            method: 'GET'
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message, applications: [] };
    }
}

async function apiGetAllApplications() {
    try {
        const response = await apiRequest('/applications/all', {
            method: 'GET'
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message, applications: [] };
    }
}

async function apiUpdateApplicationStatus(applicationId, status) {
    try {
        const response = await apiRequest(`/applications/${applicationId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message };
    }
}

async function apiGetStatistics() {
    try {
        const response = await apiRequest('/applications/statistics', {
            method: 'GET'
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message, statistics: {} };
    }
}

// ==================== EMPLOYEE API ====================

async function apiGetEmployeeActivities() {
    try {
        const response = await apiRequest('/employee/activities', {
            method: 'GET'
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message, activities: [] };
    }
}

// ==================== EMPLOYEE REQUEST API ====================

async function apiSendEmployeeRequest(requestData) {
    try {
        const response = await apiRequest('/employee/requests/send', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message };
    }
}

async function apiGetEmployeeSentRequests() {
    try {
        const response = await apiRequest('/employee/requests/my-requests', {
            method: 'GET'
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message, requests: [] };
    }
}

async function apiGetEmployeeRequestStatistics() {
    try {
        const response = await apiRequest('/employee/requests/statistics', {
            method: 'GET'
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message, statistics: {} };
    }
}

async function apiGetStudentRequests() {
    try {
        const response = await apiRequest('/student/requests', {
            method: 'GET'
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message, requests: [] };
    }
}

async function apiRespondToEmployeeRequest(requestId, status, responseMessage = '') {
    try {
        const response = await apiRequest(`/student/requests/${requestId}/respond`, {
            method: 'PUT',
            body: JSON.stringify({ status, responseMessage })
        });
        return response;
    } catch (error) {
        return { success: false, message: error.message };
    }
}

// ==================== HEALTH CHECK ====================

async function apiHealthCheck() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return await response.json();
    } catch (error) {
        console.error('Backend connection failed:', error);
        return { status: 'offline', message: 'لا يمكن الاتصال بالخادم' };
    }
}

// Check backend connectivity on page load
window.addEventListener('DOMContentLoaded', async () => {
    const health = await apiHealthCheck();
    if (health.status === 'healthy') {
        console.log('✅ Backend connected successfully');
        console.log(`📡 Backend URL: ${API_BASE_URL}`);
    } else {
        console.warn('⚠️ Backend is offline. Using fallback mode.');
        console.warn('To start backend: cd backend && python app.py');
        console.warn(`Expected backend at: ${API_BASE_URL}`);
    }
});
