// Upload Management

class UploadManager {
  constructor() {
    this.isProcessing = false;
    this.currentFile = null;
    this.uploadCount = 0;
    this.uploadCountDate = new Date().toDateString();
  }

  // Initialize upload manager
  async initialize() {
    this.loadUploadCount();
  }

  // Load upload count from localStorage
  loadUploadCount() {
    const today = new Date().toDateString();
    const stored = JSON.parse(localStorage.getItem('uploadCount') || '{}');

    if (stored.date !== today) {
      this.uploadCount = 0;
      this.uploadCountDate = today;
      localStorage.setItem('uploadCount', JSON.stringify({
        date: today,
        count: 0
      }));
    } else {
      this.uploadCount = stored.count || 0;
    }
  }

  // Increment upload count
  incrementUploadCount() {
    this.uploadCount++;
    localStorage.setItem('uploadCount', JSON.stringify({
      date: this.uploadCountDate,
      count: this.uploadCount
    }));
  }

  // Reset upload count (on tier upgrade)
  resetUploadCount() {
    this.uploadCount = 0;
    this.uploadCountDate = new Date().toDateString();
    localStorage.setItem('uploadCount', JSON.stringify({
      date: this.uploadCountDate,
      count: 0
    }));
  }

  // Get rate limit for user
  getRateLimit() {
    if (auth.isPremium()) {
      return CONFIG.RATE_LIMITS.PREMIUM;
    } else if (auth.isLoggedIn()) {
      return CONFIG.RATE_LIMITS.FREE;
    } else {
      return CONFIG.RATE_LIMITS.ANONYMOUS;
    }
  }

  // Check if user can upload
  canUpload() {
    const limit = this.getRateLimit();
    return this.uploadCount < limit;
  }

  // Get remaining uploads
  getRemainingUploads() {
    const limit = this.getRateLimit();
    return Math.max(0, limit - this.uploadCount);
  }

  // Validate file
  validateFile(file) {
    const maxSize = 25 * 1024 * 1024; // 25 MB
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Solo se permiten JPG, PNG o WEBP'
      };
    }

    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'El archivo no puede superar 25 MB'
      };
    }

    return { valid: true };
  }

  // Upload image
  async uploadImage(file) {
    if (this.isProcessing) {
      return { success: false, error: 'Procesando imagen...' };
    }

    // Validate file
    const validation = this.validateFile(file);
    if (!validation.valid) {
      return { success: false, error: validation.error };
    }

    // Check rate limit
    if (!this.canUpload()) {
      const limit = this.getRateLimit();
      return {
        success: false,
        error: `Límite diario alcanzado (${limit} uploads)`
      };
    }

    this.isProcessing = true;
    this.currentFile = file;

    try {
      const response = await api.uploadImage(file);

      if (!response.ok) {
        return {
          success: false,
          error: 'Error al procesar imagen'
        };
      }

      this.incrementUploadCount();

      // Anonymous user: return blob
      if (!auth.isLoggedIn()) {
        return {
          success: true,
          isAnonymous: true,
          blob: response.data,
          remainingUploads: this.getRemainingUploads()
        };
      }

      // Authenticated user: return image data
      return {
        success: true,
        isAnonymous: false,
        image: response.data,
        remainingUploads: this.getRemainingUploads()
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Error al subir imagen'
      };
    } finally {
      this.isProcessing = false;
    }
  }

  // Download image blob
  downloadBlob(blob, filename = 'resultado.png') {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }

  // Delete image
  async deleteImage(imageId) {
    try {
      await api.deleteImage(imageId);
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Error al eliminar imagen'
      };
    }
  }
}

// Singleton instance
const upload = new UploadManager();
