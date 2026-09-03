// API Configuration
const CONFIG = {
  // Environment
  ENVIRONMENT: (typeof process !== 'undefined' && process.env.VITE_ENVIRONMENT) || 'development',

  // API
  API_URL: (typeof process !== 'undefined' && process.env.VITE_API_URL) || 'http://localhost:8000',
  API_TIMEOUT: 30000, // 30 seconds
  API_DEBUG: (typeof process !== 'undefined' && process.env.VITE_ENVIRONMENT) === 'development',

  // Storage
  TOKEN_KEY: 'chaufondo_token',
  TOKEN_TYPE: 'bearer',

  // Rate limits (per user type)
  RATE_LIMITS: {
    ANONYMOUS: 50,    // uploads per day
    FREE: 5,           // uploads per day
    PREMIUM: 1000      // uploads per month
  },

  // File constraints
  MAX_FILE_SIZE: 25 * 1024 * 1024, // 25 MB
  ALLOWED_TYPES: ['image/jpeg', 'image/png', 'image/webp'],

  // UI
  ALERT_DURATION: 5000, // 5 seconds
  PROCESSING_DURATION: 2000 // 2 seconds simulated
};

// Helper: Get auth token from localStorage
function getAuthToken() {
  try {
    return localStorage.getItem(CONFIG.TOKEN_KEY);
  } catch (e) {
    console.warn('localStorage not available');
    return null;
  }
}

// Helper: Set auth token
function setAuthToken(token) {
  try {
    localStorage.setItem(CONFIG.TOKEN_KEY, token);
  } catch (e) {
    console.warn('localStorage not available');
  }
}

// Helper: Clear auth token
function clearAuthToken() {
  try {
    localStorage.removeItem(CONFIG.TOKEN_KEY);
  } catch (e) {
    console.warn('localStorage not available');
  }
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

// Helper: Log message (only in debug mode)
function debugLog(...args) {
  if (CONFIG.API_DEBUG) {
    console.log('[ChauFondo]', ...args);
  }
}
