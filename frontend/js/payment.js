// Payment Management

class PaymentManager {
  constructor() {
    this.isProcessing = false;
  }

  // Get payment plans
  getPlans() {
    return [
      {
        id: 'premium_month',
        name: 'Premium - 1 Mes',
        price: '$4.99 USD',
        period: 'mes',
        features: [
          '100 descargas/mes',
          'Sin marca de agua',
          'Soporte prioritario'
        ]
      },
      {
        id: 'premium_year',
        name: 'Premium - 1 Año',
        price: '$49.99 USD',
        period: 'año',
        savings: 'Ahorra 58%',
        features: [
          '1200 descargas/año',
          'Sin marca de agua',
          'Soporte prioritario',
          'Descuentos especiales'
        ]
      }
    ];
  }

  // Create subscription
  async createSubscription(planId) {
    if (this.isProcessing) return;
    this.isProcessing = true;

    try {
      const response = await api.createSubscription(planId);
      return {
        success: true,
        checkoutUrl: response.init_point,
        paymentId: response.id
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Error al crear suscripción'
      };
    } finally {
      this.isProcessing = false;
    }
  }

  // Redirect to Mercado Pago
  redirectToCheckout(checkoutUrl) {
    window.location.href = checkoutUrl;
  }

  // Check if user is premium
  isPremium() {
    return auth.isPremium();
  }

  // Get remaining days for premium
  getRemainingDays() {
    if (!auth.isPremium()) return 0;

    const expiresAt = auth.getTierExpiresAt();
    if (!expiresAt) return 0;

    const expires = new Date(expiresAt);
    const today = new Date();
    const days = Math.ceil((expires - today) / (1000 * 60 * 60 * 24));

    return Math.max(0, days);
  }
}

// Singleton instance
const payment = new PaymentManager();
