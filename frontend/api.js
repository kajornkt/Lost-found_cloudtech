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
        
        console.log(`API Request: ${config.method} ${url}`, config.body ? JSON.parse(config.body) : 'No body');
        
        try {
            const response = await fetch(url, config);
            
            console.log(`API Response: ${response.status} ${response.statusText}`);
            
            // Handle cases where response might not be JSON
            const contentType = response.headers.get('content-type');
            let data;
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }
            
            if (!response.ok) {
                throw new Error(data.detail || data.message || data || `HTTP ${response.status}: ${response.statusText}`);
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

    // Try different methods for updating user profile
    static async updateUserProfile(studentId, profileData) {
        // First try PUT
        try {
            return await this.request(`/users/${studentId}`, {
                method: 'PUT',
                body: JSON.stringify(profileData)
            });
        } catch (error) {
            console.log('PUT failed, trying PATCH...');
            // If PUT fails, try PATCH
            try {
                return await this.request(`/users/${studentId}`, {
                    method: 'PATCH',
                    body: JSON.stringify(profileData)
                });
            } catch (patchError) {
                console.log('PATCH failed, trying POST...');
                // If PATCH fails, try POST to update endpoint
                try {
                    return await this.request(`/users/${studentId}/update`, {
                        method: 'POST',
                        body: JSON.stringify(profileData)
                    });
                } catch (postError) {
                    console.log('All update methods failed');
                    throw new Error(`All update methods failed. Last error: ${postError.message}`);
                }
            }
        }
    }

    // Alternative: Try profile-specific endpoint
    static async updateUserProfileAlternative(studentId, profileData) {
        return this.request('/profile/update', {
            method: 'POST',
            body: JSON.stringify({
                student_id: studentId,
                ...profileData
            })
        });
    }

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

    // Temporary debug function - call this in console to test endpoints
    static async testEndpoints(studentId) {
        const testData = { full_name: "Test Name" };
        
        console.log('Testing endpoints...');
        
        const endpoints = [
            { method: 'PUT', url: `/users/${studentId}` },
            { method: 'PATCH', url: `/users/${studentId}` },
            { method: 'POST', url: `/users/${studentId}/update` },
            { method: 'PUT', url: '/profile' },
            { method: 'PATCH', url: '/profile' },
            { method: 'POST', url: '/profile/update' },
        ];
        
        for (let endpoint of endpoints) {
            try {
                console.log(`Trying ${endpoint.method} ${endpoint.url}`);
                const result = await this.request(endpoint.url, {
                    method: endpoint.method,
                    body: JSON.stringify(testData)
                });
                console.log(`✅ SUCCESS: ${endpoint.method} ${endpoint.url}`);
                console.log('Response:', result);
                return endpoint; // Return the working endpoint
            } catch (error) {
                console.log(`❌ FAILED: ${endpoint.method} ${endpoint.url} - ${error.message}`);
            }
        }
        
        console.log('No endpoints worked');
        return null;
    }
    
}