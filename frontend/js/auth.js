// Authentication Management

class AuthManager {
  constructor() {
    this.currentUser = null;
    this.isLoading = false;
  }

  // Initialize: check if user has token and load profile
  async initialize() {
    if (isAuthenticated()) {
      try {
        this.currentUser = await api.getCurrentUser();
        return this.currentUser;
      } catch (error) {
        console.error('Failed to load user:', error);
        clearAuthToken();
        this.currentUser = null;
      }
    }
  }

  // Signup
  async signup(email, password) {
    if (this.isLoading) return;
    this.isLoading = true;

    try {
      const response = await api.signup(email, password);
      setAuthToken(response.access_token);
      this.currentUser = await api.getCurrentUser();
      return { success: true, user: this.currentUser };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Signup failed'
      };
    } finally {
      this.isLoading = false;
    }
  }

  // Login
  async login(email, password) {
    if (this.isLoading) return;
    this.isLoading = true;

    try {
      const response = await api.login(email, password);
      setAuthToken(response.access_token);
      this.currentUser = await api.getCurrentUser();
      return { success: true, user: this.currentUser };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Login failed'
      };
    } finally {
      this.isLoading = false;
    }
  }

  // Logout
  logout() {
    clearAuthToken();
    this.currentUser = null;
  }

  // Check if user is authenticated
  isLoggedIn() {
    return !!this.currentUser;
  }

  // Get current user
  getUser() {
    return this.currentUser;
  }

  // Check if user is premium
  isPremium() {
    return this.currentUser?.tier === 'premium';
  }

  // Get tier expires at
  getTierExpiresAt() {
    return this.currentUser?.tier_expires_at;
  }
}

// Singleton instance
const auth = new AuthManager();
