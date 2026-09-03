// UI Management

class UIManager {
  constructor() {
    this.currentPage = 'landing';
    this.isAuthMode = 'signup';
    this.currentResultBlob = null;
    this.currentResultImage = null;
  }

  // Initialize UI
  async initialize() {
    await upload.initialize();
    this.setupEventListeners();
    await this.checkAuthStatus();
    this.render();

    if (auth.isLoggedIn()) {
      await this.loadDashboard();
    }
  }

  // Setup all event listeners
  setupEventListeners() {
    // Auth form
    const authForm = document.getElementById('authForm');
    if (authForm) {
      authForm.addEventListener('submit', (e) => this.handleAuthSubmit(e));
    }

    // Landing upload area
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
      uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
      uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
      uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
      uploadArea.addEventListener('click', () => this.triggerFileInput());
    }

    // Dashboard upload area
    const dashboardUploadArea = document.getElementById('dashboardUploadArea');
    if (dashboardUploadArea) {
      dashboardUploadArea.addEventListener('drop', (e) => this.handleDashboardDrop(e));
      dashboardUploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
      dashboardUploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
      dashboardUploadArea.addEventListener('click', () => this.triggerDashboardFileInput());
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
    this.currentPage = auth.isLoggedIn() ? 'dashboard' : 'landing';
  }

  // Render current page
  render() {
    const pages = document.querySelectorAll('[data-page]');
    pages.forEach(page => page.classList.remove('active'));

    const currentPageEl = document.querySelector(`[data-page="${this.currentPage}"]`);
    if (currentPageEl) {
      currentPageEl.classList.add('active');
    }

    this.updateAuthUI();
  }

  // Update auth UI elements
  updateAuthUI() {
    const authButtons = document.querySelectorAll('[data-auth-only]');
    const anonButtons = document.querySelectorAll('[data-anon-only]');

    if (auth.isLoggedIn()) {
      authButtons.forEach(btn => btn.classList.remove('hidden'));
      anonButtons.forEach(btn => btn.classList.add('hidden'));

      const userEmail = document.getElementById('userEmail');
      if (userEmail) {
        userEmail.textContent = auth.getUser()?.email || '';
      }

      this.updateDashboardUI();
    } else {
      authButtons.forEach(btn => btn.classList.add('hidden'));
      anonButtons.forEach(btn => btn.classList.remove('hidden'));
    }
  }

  // Update dashboard UI
  updateDashboardUI() {
    const user = auth.getUser();
    if (!user) return;

    // Update tier badge
    const tierBadge = document.getElementById('userTier');
    if (tierBadge) {
      if (payment.isPremium()) {
        const days = payment.getRemainingDays();
        tierBadge.textContent = `Premium (${days} días)`;
        tierBadge.className = 'user-tier premium';
      } else {
        tierBadge.textContent = 'Free';
        tierBadge.className = 'user-tier';
      }
    }

    // Update upload count
    const uploadCount = document.getElementById('uploadCount');
    const uploadLimit = document.getElementById('uploadLimit');
    if (uploadCount && uploadLimit) {
      uploadCount.textContent = upload.uploadCount;
      uploadLimit.textContent = upload.getRateLimit();
    }

    // Show/hide upgrade button
    const upgradeBtn = document.getElementById('upgradeBtn');
    if (upgradeBtn) {
      if (!payment.isPremium()) {
        upgradeBtn.style.display = 'block';
      } else {
        upgradeBtn.style.display = 'none';
      }
    }
  }

  // Load dashboard data
  async loadDashboard() {
    try {
      const images = await api.getImages();
      this.renderImageGrid(images);
      this.updateDashboardUI();
    } catch (error) {
      console.error('Error loading images:', error);
    }
  }

  // Render image grid
  renderImageGrid(images) {
    const grid = document.getElementById('imagesGrid');
    if (!grid) return;

    if (!images || images.length === 0) {
      grid.innerHTML = `
        <p style="grid-column: 1/-1; text-align: center; color: #999; padding: 40px;">
          Aún no tienes imágenes. ¡Sube una para comenzar!
        </p>
      `;
      return;
    }

    grid.innerHTML = images.map(img => `
      <div class="image-card">
        <img src="${img.processed_url || img.original_url}" alt="Imagen">
        <div class="image-card-footer">
          <button class="btn-download" onclick="ui.downloadImage('${img.id}', '${img.processed_url || img.original_url}')">
            Descargar
          </button>
          <button class="btn-delete" onclick="ui.deleteImage('${img.id}')">
            Eliminar
          </button>
        </div>
      </div>
    `).join('');
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

  // Update auth modal
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

  // Toggle auth mode
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

    if (!email || !password || password.length < 8) {
      this.showError('Email válido y contraseña (mín. 8 caracteres) requeridos');
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
      document.getElementById('authForm').reset();
      setTimeout(() => {
        this.navigateToPage('dashboard');
        this.loadDashboard();
      }, 1500);
    } else {
      this.showError(result.error || 'Error en autenticación');
    }
  }

  // Handle file drop (landing)
  handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      this.handleFile(files[0], 'landing');
    }
  }

  // Handle file drop (dashboard)
  handleDashboardDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      this.handleFile(files[0], 'dashboard');
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

  // Trigger file input
  triggerFileInput() {
    document.getElementById('fileInput').click();
  }

  // Trigger dashboard file input
  triggerDashboardFileInput() {
    const input = document.getElementById('dashboardFileInput');
    if (!input) {
      const fileInput = document.createElement('input');
      fileInput.id = 'dashboardFileInput';
      fileInput.type = 'file';
      fileInput.accept = 'image/jpeg,image/png,image/webp';
      fileInput.style.display = 'none';
      fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
          this.handleFile(e.target.files[0], 'dashboard');
        }
      });
      document.body.appendChild(fileInput);
      fileInput.click();
    } else {
      input.click();
    }
  }

  // Handle file select
  handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
      this.handleFile(files[0], 'landing');
    }
  }

  // Handle file upload
  async handleFile(file, page) {
    const isLanding = page === 'landing';
    this.showProcessing(isLanding);

    const result = await upload.uploadImage(file);

    if (!result.success) {
      this.hideProcessing(isLanding);
      this.showError(result.error);
      return;
    }

    // Simulate processing
    await new Promise(resolve => setTimeout(resolve, 2000));

    if (result.isAnonymous) {
      this.currentResultBlob = result.blob;
      this.hideProcessing(isLanding);
      this.showAnonymousResult();
    } else {
      this.currentResultImage = result.image;
      this.hideProcessing(isLanding);
      this.showAuthenticatedResult(result.image, isLanding);
      await this.loadDashboard();
    }
  }

  // Show processing state
  showProcessing(isLanding = true) {
    if (isLanding) {
      const uploadState = document.getElementById('uploadState');
      const processingState = document.getElementById('processingState');
      if (uploadState) uploadState.classList.add('hidden');
      if (processingState) processingState.classList.remove('hidden');
    } else {
      const uploadState = document.getElementById('dashboardUploadState');
      const processingState = document.getElementById('dashboardProcessingState');
      if (uploadState) uploadState.classList.add('hidden');
      if (processingState) processingState.classList.remove('hidden');
    }
  }

  // Hide processing state
  hideProcessing(isLanding = true) {
    if (isLanding) {
      const processingState = document.getElementById('processingState');
      if (processingState) processingState.classList.add('hidden');
    } else {
      const processingState = document.getElementById('dashboardProcessingState');
      if (processingState) processingState.classList.add('hidden');
    }
  }

  // Show anonymous result
  showAnonymousResult() {
    const resultState = document.getElementById('resultState');
    if (resultState) resultState.classList.remove('hidden');
    this.showSuccess('Imagen procesada. Descargando...');
  }

  // Show authenticated result
  showAuthenticatedResult(image, isLanding = true) {
    if (isLanding) {
      const resultState = document.getElementById('resultState');
      if (resultState) resultState.classList.remove('hidden');
      const preview = document.getElementById('previewImage');
      if (preview && image.processed_url) {
        preview.src = image.processed_url;
        preview.style.display = 'block';
      }
    } else {
      const resultState = document.getElementById('dashboardResultState');
      if (resultState) resultState.classList.remove('hidden');
      const preview = document.getElementById('dashboardPreviewImage');
      if (preview && image.processed_url) {
        preview.src = image.processed_url;
        preview.style.display = 'block';
      }
    }
    this.showSuccess('Imagen guardada exitosamente');
  }

  // Download result (landing)
  downloadResult() {
    if (this.currentResultBlob) {
      upload.downloadBlob(this.currentResultBlob);
    }
  }

  // Download result (dashboard)
  downloadDashboardResult() {
    if (this.currentResultImage?.processed_url) {
      this.downloadImage('result', this.currentResultImage.processed_url);
    }
  }

  // Download image from URL
  async downloadImage(imageId, imageUrl) {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      upload.downloadBlob(blob, `chaufondo-${Date.now()}.png`);
    } catch (error) {
      this.showError('Error al descargar imagen');
    }
  }

  // Delete image
  async deleteImage(imageId) {
    if (!confirm('¿Eliminar esta imagen?')) return;

    const result = await upload.deleteImage(imageId);
    if (result.success) {
      this.showSuccess('Imagen eliminada');
      await this.loadDashboard();
    } else {
      this.showError(result.error);
    }
  }

  // Reset upload (landing)
  resetUpload() {
    const uploadState = document.getElementById('uploadState');
    const resultState = document.getElementById('resultState');
    if (uploadState) uploadState.classList.remove('hidden');
    if (resultState) resultState.classList.add('hidden');
    document.getElementById('fileInput').value = '';
    this.currentResultBlob = null;
  }

  // Reset upload (dashboard)
  resetDashboardUpload() {
    const uploadState = document.getElementById('dashboardUploadState');
    const resultState = document.getElementById('dashboardResultState');
    if (uploadState) uploadState.classList.remove('hidden');
    if (resultState) resultState.classList.add('hidden');
    this.currentResultImage = null;
  }

  // Show payment modal
  showPaymentModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h2>Upgrade a Premium</h2>
          <button onclick="this.closest('.modal-overlay').remove()" style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
        </div>
        <div class="modal-body">
          <div class="plans-grid">
            ${payment.getPlans().map(plan => `
              <div class="plan-card">
                <h3>${plan.name}</h3>
                <div class="plan-price">${plan.price}</div>
                ${plan.savings ? `<div class="plan-savings">${plan.savings}</div>` : ''}
                <ul class="plan-features">
                  ${plan.features.map(f => `<li>✓ ${f}</li>`).join('')}
                </ul>
                <button class="btn-primary" style="width: 100%;" onclick="ui.startCheckout('${plan.id}')">
                  Elegir plan
                </button>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  // Start checkout
  async startCheckout(planId) {
    const button = event.target;
    button.disabled = true;
    button.textContent = 'Redirigiendo...';

    const result = await payment.createSubscription(planId);

    if (result.success) {
      payment.redirectToCheckout(result.checkoutUrl);
    } else {
      this.showError(result.error);
      button.disabled = false;
      button.textContent = 'Elegir plan';
    }
  }

  // Show error
  showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.textContent = message;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
  }

  // Show success
  showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success';
    alert.textContent = message;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 4000);
  }

  // Logout
  logout() {
    auth.logout();
    upload.resetUploadCount();
    this.navigateToPage('landing');
    this.showSuccess('Sesión cerrada');
  }
}

const ui = new UIManager();
