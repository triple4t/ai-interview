const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface User {
    id: number;
    email: string;
    username: string;
    full_name?: string;
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
    updated_at?: string;
}

export interface SignupData {
    email: string;
    username: string;
    password: string;
    full_name?: string;
}

export interface LoginData {
    email: string;
    password: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
}

export interface ApiError {
    detail: string;
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const config: RequestInit = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        // Add auth token if available
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('auth_token');
            if (token) {
                config.headers = {
                    ...config.headers,
                    'Authorization': `Bearer ${token}`,
                };
            }
        }

        try {
            const response = await fetch(url, config);
            console.log(`API Response Status: ${response.status}`); // Debug log

            if (!response.ok) {
                let errorMessage = `HTTP error! status: ${response.status}`;

                try {
                    const errorData: ApiError = await response.json();
                    console.log('API Error Data:', errorData); // Debug log
                    errorMessage = errorData.detail || errorMessage;
                } catch (parseError) {
                    // If we can't parse the error response, use a generic message based on status
                    switch (response.status) {
                        case 400:
                            errorMessage = 'Bad request. Please check your input.';
                            break;
                        case 401:
                            errorMessage = 'Unauthorized. Please check your credentials.';
                            break;
                        case 403:
                            errorMessage = 'Forbidden. You don\'t have permission to perform this action.';
                            break;
                        case 404:
                            errorMessage = 'Resource not found.';
                            break;
                        case 422:
                            errorMessage = 'Validation error. Please check your input.';
                            break;
                        case 500:
                            errorMessage = 'Server error. Please try again later.';
                            break;
                        default:
                            errorMessage = `Server error (${response.status}). Please try again later.`;
                    }
                }

                throw new Error(errorMessage);
            }

            return response.json();
        } catch (error) {
            // Handle network errors
            if (error instanceof TypeError && error.message.includes('fetch')) {
                throw new Error('Network error. Please check your connection and try again.');
            }
            throw error;
        }
    }

    // Auth endpoints
    async signup(data: SignupData): Promise<User> {
        return this.request<User>('/auth/signup', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async login(data: LoginData): Promise<AuthResponse> {
        return this.request<AuthResponse>('/auth/login', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // User endpoints
    async getCurrentUser(): Promise<User> {
        // Check if we have an auth token before making the request
        if (!this.isAuthenticated()) {
            throw new Error('Not authenticated');
        }
        return this.request<User>('/users/me');
    }

    async updateUser(data: Partial<User>): Promise<User> {
        return this.request<User>('/users/me', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteUser(): Promise<{ message: string }> {
        return this.request<{ message: string }>('/users/me', {
            method: 'DELETE',
        });
    }

    // Resume endpoints
    async uploadResume(file: File): Promise<{ message: string; filename: string; user_id: string }> {
        const formData = new FormData();
        formData.append('file', file);

        const url = `${this.baseUrl}/resume/upload`;
        const token = this.getAuthToken();

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to upload resume');
        }

        return response.json();
    }

    async getJobMatches(threshold: number = 0.6): Promise<{ matches: any[]; total_matches: number; threshold: number; user_id: string }> {
        return this.request<{ matches: any[]; total_matches: number; threshold: number; user_id: string }>(`/resume/match-jds?threshold=${threshold}`);
    }

    async getJdContent(jdFilename: string): Promise<{ filename: string; content: string }> {
        return this.request<{ filename: string; content: string }>(`/resume/jd/${jdFilename}`);
    }

    async getResumeStatus(): Promise<{ has_resume: boolean; user_id: string }> {
        return this.request<{ has_resume: boolean; user_id: string }>('/resume/resume-status');
    }

    // Utility methods
    setAuthToken(token: string) {
        if (typeof window !== 'undefined') {
            localStorage.setItem('auth_token', token);
        }
    }

    removeAuthToken() {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
        }
    }

    getAuthToken(): string | null {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('auth_token');
        }
        return null;
    }

    isAuthenticated(): boolean {
        return !!this.getAuthToken();
    }
}

export const apiClient = new ApiClient(API_BASE_URL); 