// UI Management

class UIManager {
  constructor() {
    this.currentPage = 'landing';
    this.isAuthMode = 'signup'; // signup or login
  }

  // Initialize UI
  async initialize() {
    this.setupEventListeners();
    await this.checkAuthStatus();
    this.render();
  }

  // Setup all event listeners
  setupEventListeners() {
    // Auth form
    const authForm = document.getElementById('authForm');
    if (authForm) {
      authForm.addEventListener('submit', (e) => this.handleAuthSubmit(e));
    }

    // Upload area
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
      uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
      uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
      uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
      uploadArea.addEventListener('click', () => this.triggerFileInput());
    }

    // File input
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
      fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
    }
  }

  // Check authentication status
  async checkAuthStatus() {
    await auth.initialize();
    if (auth.isLoggedIn()) {
      this.currentPage = 'dashboard';
    } else {
      this.currentPage = 'landing';
    }
  }

  // Render current page
  render() {
    const pages = document.querySelectorAll('[data-page]');
    pages.forEach(page => {
      page.classList.remove('active');
    });

    const currentPageEl = document.querySelector(`[data-page="${this.currentPage}"]`);
    if (currentPageEl) {
      currentPageEl.classList.add('active');
    }

    // Update UI based on auth status
    this.updateAuthUI();
  }

  // Update auth UI elements
  updateAuthUI() {
    const authButtons = document.querySelectorAll('[data-auth-only]');
    const anonButtons = document.querySelectorAll('[data-anon-only]');

    if (auth.isLoggedIn()) {
      authButtons.forEach(btn => btn.classList.remove('hidden'));
      anonButtons.forEach(btn => btn.classList.add('hidden'));

      // Update user info
      const userEmail = document.getElementById('userEmail');
      if (userEmail) {
        userEmail.textContent = auth.getUser()?.email || '';
      }
    } else {
      authButtons.forEach(btn => btn.classList.add('hidden'));
      anonButtons.forEach(btn => btn.classList.remove('hidden'));
    }
  }

  // Navigate to page
  navigateToPage(page) {
    this.currentPage = page;
    this.render();
    window.scrollTo(0, 0);
  }

  // Show auth modal
  showAuthModal(mode = 'signup') {
    this.isAuthMode = mode;
    this.updateAuthModal();
    this.navigateToPage('auth');
  }

  // Update auth modal title/button
  updateAuthModal() {
    const title = document.getElementById('authTitle');
    const button = document.getElementById('authSubmitBtn');
    const toggle = document.getElementById('authToggle');

    if (this.isAuthMode === 'signup') {
      if (title) title.textContent = 'Crea una cuenta';
      if (button) button.textContent = 'Registrarse';
      if (toggle) toggle.innerHTML = '¿Ya tienes cuenta? <a href="#" onclick="ui.toggleAuthMode(event)">Inicia sesión</a>';
    } else {
      if (title) title.textContent = 'Inicia sesión';
      if (button) button.textContent = 'Inicia sesión';
      if (toggle) toggle.innerHTML = '¿No tienes cuenta? <a href="#" onclick="ui.toggleAuthMode(event)">Registrarse</a>';
    }
  }

  // Toggle between signup/login
  toggleAuthMode(e) {
    e.preventDefault();
    this.isAuthMode = this.isAuthMode === 'signup' ? 'login' : 'signup';
    this.updateAuthModal();
  }

  // Handle auth submit
  async handleAuthSubmit(e) {
    e.preventDefault();

    const email = document.getElementById('authEmail').value;
    const password = document.getElementById('authPassword').value;

    if (!email || !password) {
      this.showError('Por favor completa los campos');
      return;
    }

    const button = document.getElementById('authSubmitBtn');
    button.disabled = true;
    button.textContent = 'Procesando...';

    let result;
    if (this.isAuthMode === 'signup') {
      result = await auth.signup(email, password);
    } else {
      result = await auth.login(email, password);
    }

    button.disabled = false;
    button.textContent = this.isAuthMode === 'signup' ? 'Registrarse' : 'Inicia sesión';

    if (result.success) {
      this.showSuccess(`${this.isAuthMode === 'signup' ? 'Cuenta creada' : 'Sesión iniciada'} exitosamente`);
      setTimeout(() => {
        this.navigateToPage('dashboard');
      }, 1000);
    } else {
      this.showError(result.error);
    }
  }

  // Handle file drop
  handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      this.handleFile(files[0]);
    }
  }

  // Handle drag over
  handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
  }

  // Handle drag leave
  handleDragLeave(e) {
    e.currentTarget.classList.remove('dragover');
  }

  // Trigger file input click
  triggerFileInput() {
    document.getElementById('fileInput').click();
  }

  // Handle file select
  handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
      this.handleFile(files[0]);
    }
  }

  // Handle file upload
  async handleFile(file) {
    this.showProcessing();

    const result = await upload.uploadImage(file);

    if (!result.success) {
      this.hideProcessing();
      this.showError(result.error);
      return;
    }

    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 2000));

    if (result.isAnonymous) {
      // Download PNG for anonymous user
      upload.downloadBlob(result.blob);
      this.hideProcessing();
      this.showAnonymousResult();
    } else {
      // Show result for authenticated user
      this.hideProcessing();
      this.showAuthenticatedResult(result.image);
    }
  }

  // Show processing state
  showProcessing() {
    const uploadState = document.getElementById('uploadState');
    const processingState = document.getElementById('processingState');

    if (uploadState) uploadState.classList.add('hidden');
    if (processingState) processingState.classList.remove('hidden');
  }

  // Hide processing state
  hideProcessing() {
    const processingState = document.getElementById('processingState');
    if (processingState) processingState.classList.add('hidden');
  }

  // Show anonymous result
  showAnonymousResult() {
    const resultState = document.getElementById('resultState');
    if (resultState) resultState.classList.remove('hidden');

    this.showSuccess('Imagen procesada. ¿Quieres crear cuenta para guardar tu historial?');
  }

  // Show authenticated result
  showAuthenticatedResult(image) {
    const resultState = document.getElementById('resultState');
    if (resultState) resultState.classList.remove('hidden');

    // Show preview image
    const preview = document.getElementById('previewImage');
    if (preview && image.processed_url) {
      preview.src = image.processed_url;
      preview.style.display = 'block';
    }
  }

  // Show error message
  showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.textContent = message;
    document.body.appendChild(alert);

    setTimeout(() => alert.remove(), 5000);
  }

  // Show success message
  showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success';
    alert.textContent = message;
    document.body.appendChild(alert);

    setTimeout(() => alert.remove(), 5000);
  }

  // Logout
  logout() {
    auth.logout();
    this.navigateToPage('landing');
    this.showSuccess('Sesión cerrada');
  }
}

// Singleton instance
const ui = new UIManager();
