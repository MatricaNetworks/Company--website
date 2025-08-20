/**
 * API utility functions for Matrica Networks
 * Handles all backend communications and data management
 */

class MatricaAPI {
    constructor() {
        this.baseURL = '';
        this.csrfToken = null;
        this.init();
    }

    async init() {
        await this.getCSRFToken();
    }

    // CSRF Token Management
    async getCSRFToken() {
        try {
            const response = await fetch('/api/csrf-token');
            if (response.ok) {
                const data = await response.json();
                this.csrfToken = data.token;
            }
        } catch (error) {
            console.error('Failed to get CSRF token:', error);
        }
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body.csrf_token = this.csrfToken;
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(endpoint, config);
            
            if (response.status === 401) {
                window.location.href = '/portal/login.html?session_expired=true';
                return null;
            }

            return response;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Authentication endpoints
    async login(credentials) {
        return await this.request('/api/auth/login', {
            method: 'POST',
            body: credentials
        });
    }

    async logout() {
        return await this.request('/api/auth/logout', {
            method: 'POST',
            body: {}
        });
    }

    async getCurrentUser() {
        return await this.request('/api/me');
    }

    // Employee endpoints
    async getEmployees() {
        return await this.request('/api/employees');
    }

    async createEmployee(employeeData) {
        return await this.request('/api/employees', {
            method: 'POST',
            body: employeeData
        });
    }

    async updateEmployee(id, employeeData) {
        return await this.request(`/api/employees/${id}`, {
            method: 'PUT',
            body: employeeData
        });
    }

    async deleteEmployee(id) {
        return await this.request(`/api/employees/${id}`, {
            method: 'DELETE',
            body: {}
        });
    }

    // Blog endpoints
    async getBlogs(params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.request(`/api/blogs${query ? '?' + query : ''}`);
    }

    async getBlog(id) {
        return await this.request(`/api/blogs/${id}`);
    }

    async createBlog(blogData) {
        return await this.request('/api/blogs', {
            method: 'POST',
            body: blogData
        });
    }

    async updateBlog(id, blogData) {
        return await this.request(`/api/blogs/${id}`, {
            method: 'PUT',
            body: blogData
        });
    }

    async deleteBlog(id) {
        return await this.request(`/api/blogs/${id}`, {
            method: 'DELETE',
            body: {}
        });
    }

    // Contact endpoints
    async submitContact(contactData) {
        return await this.request('/api/contact', {
            method: 'POST',
            body: contactData
        });
    }

    // Attendance endpoints
    async clockIn() {
        return await this.request('/api/attendance/clock-in', {
            method: 'POST',
            body: {}
        });
    }

    async clockOut() {
        return await this.request('/api/attendance/clock-out', {
            method: 'POST',
            body: {}
        });
    }

    async getAttendanceHistory() {
        return await this.request('/api/attendance/my');
    }

    // Leave endpoints
    async applyLeave(leaveData) {
        return await this.request('/api/leave/apply', {
            method: 'POST',
            body: leaveData
        });
    }

    async getLeaveRequests() {
        return await this.request('/api/leave/my');
    }

    async updateLeaveRequest(id, status) {
        return await this.request(`/api/leave/${id}`, {
            method: 'PUT',
            body: { status }
        });
    }

    // Task endpoints
    async getTasks() {
        return await this.request('/api/tasks/my');
    }

    async updateTaskProgress(id, progress) {
        return await this.request(`/api/tasks/${id}/progress`, {
            method: 'PUT',
            body: { progress }
        });
    }

    // Document endpoints
    async getDocuments() {
        return await this.request('/api/documents');
    }

    async downloadDocument(type) {
        window.open(`/api/documents/${type}`, '_blank');
    }

    // Audit endpoints
    async getAuditLog(params = {}) {
        const query = new URLSearchParams(params).toString();
        return await this.request(`/api/audit${query ? '?' + query : ''}`);
    }
}

// Create global API instance
window.api = new MatricaAPI();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MatricaAPI;
}