import * as SecureStore from 'expo-secure-store';

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    private async getAuthToken(): Promise<string | null> {
        try {
            return await SecureStore.getItemAsync('access_token');
        } catch (error) {
            console.error('Error getting auth token:', error);
            return null;
        }
    }

    private async makeRequest(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<Response> {
        const token = await this.getAuthToken();
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>),
        };

        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }

        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            ...options,
            headers,
        });

        return response;
    }

    async get(endpoint: string): Promise<Response> {
        return this.makeRequest(endpoint, { method: 'GET' });
    }

    async post(endpoint: string, data?: any): Promise<Response> {
        const options: RequestInit = { method: 'POST' };
        if (data) {
            options.body = JSON.stringify(data);
        }
        return this.makeRequest(endpoint, options);
    }

    async put(endpoint: string, data?: any): Promise<Response> {
        const options: RequestInit = { method: 'PUT' };
        if (data) {
            options.body = JSON.stringify(data);
        }
        return this.makeRequest(endpoint, options);
    }

    async delete(endpoint: string): Promise<Response> {
        return this.makeRequest(endpoint, { method: 'DELETE' });
    }

    async patch(endpoint: string, data?: any): Promise<Response> {
        const options: RequestInit = { method: 'PATCH' };
        if (data) {
            options.body = JSON.stringify(data);
        }
        return this.makeRequest(endpoint, options);
    }
}

export const apiClient = new ApiClient();
