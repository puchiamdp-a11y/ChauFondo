// API Wrapper - All HTTP calls to backend

class APIClient {
  constructor() {
    this.baseUrl = CONFIG.API_URL;
    this.timeout = 30000; // 30 seconds
    this.retries = 3;
    this.retryDelay = 1000;
  }

  // Log API calls (for debugging)
  log(method, endpoint, status, message) {
    if (CONFIG.API_DEBUG) {
      console.log(`[API] ${method} ${endpoint} - ${status} ${message}`);
    }
  }

  // Helper: Make HTTP request with retry logic
  async request(endpoint, options = {}, retryCount = 0) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      ...options.headers,
      ...getAuthHeader()
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      // Handle non-JSON responses (like PNG)
      if (response.headers.get('content-type')?.includes('image')) {
        if (!response.ok) {
          throw new APIError(response.status, 'Fallo al procesar imagen');
        }
        this.log(options.method || 'GET', endpoint, response.status, 'OK');
        return {
          ok: response.ok,
          status: response.status,
          data: await response.blob()
        };
      }

      // Try to parse JSON
      let data;
      try {
        data = await response.json();
      } catch {
        data = { detail: 'Invalid response from server' };
      }

      if (!response.ok) {
        const errorMsg = typeof data?.detail === 'string'
          ? data.detail
          : data?.message || 'API Error';
        throw new APIError(response.status, errorMsg);
      }

      this.log(options.method || 'GET', endpoint, response.status, 'OK');

      return {
        ok: response.ok,
        status: response.status,
        data
      };
    } catch (error) {
      if (error instanceof APIError) {
        this.log(options.method || 'GET', endpoint, error.status, error.message);
        throw error;
      }

      // Network error or timeout
      if (error.name === 'AbortError') {
        throw new APIError(0, 'Request timeout - El servidor no responde');
      }

      if (error instanceof TypeError) {
        throw new APIError(0, 'Error de conexión - Verifica tu internet');
      }

      this.log(options.method || 'GET', endpoint, 'ERROR', error.message);
      throw new APIError(0, error.message);
    }
  }

  // Validate API is reachable
  async validateConnection() {
    try {
      await this.healthCheck();
      return { ok: true };
    } catch (error) {
      return {
        ok: false,
        error: `No se puede conectar a ${this.baseUrl}: ${error.message}`
      };
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

  get isNetworkError() {
    return this.status === 0;
  }

  get isAuthError() {
    return this.status === 401;
  }

  get isNotFoundError() {
    return this.status === 404;
  }

  get isServerError() {
    return this.status >= 500;
  }
}

// Singleton instance
const api = new APIClient();
