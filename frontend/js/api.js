// API Wrapper - All HTTP calls to backend

class APIClient {
  constructor() {
    this.baseUrl = CONFIG.API_URL;
  }

  // Helper: Make HTTP request
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      ...options.headers,
      ...getAuthHeader()
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      // Handle non-JSON responses (like PNG)
      if (response.headers.get('content-type')?.includes('image')) {
        return {
          ok: response.ok,
          status: response.status,
          data: await response.blob()
        };
      }

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(response.status, data.detail || 'API Error');
      }

      return {
        ok: response.ok,
        status: response.status,
        data
      };
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError(0, error.message);
    }
  }

  // AUTH ENDPOINTS
  async signup(email, password) {
    const response = await this.request('/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return response.data;
  }

  async login(email, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.request('/auth/me', {
      method: 'GET'
    });
    return response.data;
  }

  // UPLOAD ENDPOINTS
  async uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.request('/images/upload', {
      method: 'POST',
      body: formData
      // Don't set Content-Type header - browser will set it with boundary
    });

    return response;
  }

  async getImages() {
    const response = await this.request('/images', {
      method: 'GET'
    });
    return response.data;
  }

  async deleteImage(imageId) {
    const response = await this.request(`/images/${imageId}`, {
      method: 'DELETE'
    });
    return response.data;
  }

  async downloadImage(imageId) {
    const response = await this.request(`/images/${imageId}/download`, {
      method: 'GET'
    });
    return response;
  }

  // PAYMENT ENDPOINTS
  async createSubscription(plan) {
    const response = await this.request('/payment/create-subscription', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plan })
    });
    return response.data;
  }

  // HEALTH CHECK
  async healthCheck() {
    const response = await this.request('/health', {
      method: 'GET'
    });
    return response.data;
  }
}

// Custom Error class
class APIError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.name = 'APIError';
  }
}

// Singleton instance
const api = new APIClient();
