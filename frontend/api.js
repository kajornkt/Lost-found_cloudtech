// api.js
const API_BASE = "http://localhost:8000";

class LostFoundAPI {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            // Handle cases where response might not be JSON
            const contentType = response.headers.get('content-type');
            let data;
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }
            
            if (!response.ok) {
                throw new Error(data.detail || data || 'API request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth endpoints
    static async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    static async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    // Posts endpoints
    static async getPosts(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/posts?${params}`);
    }

    static async createPost(postData) {
        return this.request('/posts', {
            method: 'POST',
            body: JSON.stringify(postData)
        });
    }

    static async getUserPosts(studentId) {
        return this.request(`/posts/user/${studentId}`);
    }

    static async getPostDetails(postId) {
        return this.request(`/posts/${postId}`);
    }

    // User endpoints
    static async getUserProfile(studentId) {
        return this.request(`/users/${studentId}`);
    }
    
    // Add to your existing LostFoundAPI class in api.js

    // Update post status
    static async updatePostStatus(postId, statusData) {
    return this.request(`/posts/${postId}`, {
        method: 'PUT',
        body: JSON.stringify(statusData)
    });
    }

    // Delete post
    static async deletePost(postId) {
        return this.request(`/posts/${postId}`, {
            method: 'DELETE'
        });
    }
}