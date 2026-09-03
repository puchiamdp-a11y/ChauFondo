// API Configuration
const CONFIG = {
  API_URL: process.env.VITE_API_URL || 'http://localhost:8000',
  TOKEN_KEY: 'chaufondo_token',
  TOKEN_TYPE: 'bearer',

  // Rate limits
  RATE_LIMITS: {
    ANONYMOUS: 50,    // uploads per day
    FREE: 5,           // uploads per day
    PREMIUM: 1000      // uploads per month
  }
};

// Helper: Get auth token from localStorage
function getAuthToken() {
  return localStorage.getItem(CONFIG.TOKEN_KEY);
}

// Helper: Set auth token
function setAuthToken(token) {
  localStorage.setItem(CONFIG.TOKEN_KEY, token);
}

// Helper: Clear auth token
function clearAuthToken() {
  localStorage.removeItem(CONFIG.TOKEN_KEY);
}

// Helper: Check if user is authenticated
function isAuthenticated() {
  return !!getAuthToken();
}

// Helper: Get Authorization header
function getAuthHeader() {
  const token = getAuthToken();
  if (token) {
    return {
      'Authorization': `Bearer ${token}`
    };
  }
  return {};
}
