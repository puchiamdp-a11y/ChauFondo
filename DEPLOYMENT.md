# ChauFondo Backend - Deployment Guide

## Quick Start with Railway

### Prerequisites
- Railway account: https://railway.app
- PostgreSQL database (Railway plugin)
- Mercado Pago API credentials
- GitHub repository connected to Railway

### Step 1: Create Railway Project

1. Go to https://railway.app/dashboard
2. Click "New Project" → "Deploy from GitHub repo"
3. Select the `puchiamdp-a11y/ChauFondo` repository
4. Railway will auto-detect the Dockerfile and deploy

### Step 2: Add PostgreSQL Database

1. In Railway dashboard, click "Add Service" → "PostgreSQL"
2. Railway automatically sets `DATABASE_URL` environment variable
3. Migration: The app will auto-create tables on first run

### Step 3: Configure Environment Variables

1. In Railway dashboard, go to your service settings
2. Add all variables from `.env.railway`:

```
JWT_SECRET=<generate-with-secrets>
MERCADO_PAGO_TOKEN=<your-token>
MERCADO_PAGO_SECRET=<your-secret>
MERCADO_PAGO_PUBLIC_KEY=<your-public-key>
API_BASE_URL=https://<your-railway-domain>.railway.app
FRONTEND_URL=https://<your-frontend-domain>
CORS_ORIGINS=https://<your-frontend-domain>
ENVIRONMENT=production
```

### Step 4: Configure Mercado Pago Webhooks

1. Go to Mercado Pago settings: https://www.mercadopago.com.ar/account/notifications
2. Add webhook URL: `https://<your-railway-domain>.railway.app/payments/webhook`
3. Subscribe to: `payment.created` and `payment.updated` events
4. Copy the webhook secret to `MERCADO_PAGO_SECRET` env var

### Step 5: Verify Deployment

```bash
# Check API health
curl https://<your-railway-domain>.railway.app/health

# Response should be:
# {"status": "ok", "db": "connected"}
```

### Step 6: Frontend Configuration

Update your frontend `.env`:
```
VITE_API_URL=https://<your-railway-domain>.railway.app
VITE_MERCADO_PAGO_PUBLIC_KEY=<your-public-key>
```

## Database Migrations

The application automatically creates tables on first run via SQLAlchemy's `Base.metadata.create_all()`.

For future schema changes:
1. Modify models in `app/models.py`
2. Restart the Railway service
3. App will create/update tables automatically

## Monitoring

### Health Check
- Endpoint: `GET /health`
- Returns database connection status
- Railway uses this for auto-restart on failure

### Logs
- View logs in Railway dashboard: Service → Logs tab
- Production logs include all API requests and errors

### Error Tracking
Consider integrating Sentry:
```python
import sentry_sdk
sentry_sdk.init("your-sentry-dsn", environment="production")
```

## Troubleshooting

### 502 Bad Gateway
- Check DATABASE_URL is correctly set
- Verify PostgreSQL service is running
- Check logs for connection errors

### 401 Unauthorized
- Verify JWT_SECRET is set (must be 32+ characters)
- Check token expiration (JWT_EXPIRATION_HOURS)

### Webhook not processing
- Verify MERCADO_PAGO_SECRET is set
- Check X-Signature header in Mercado Pago logs
- Ensure API_BASE_URL matches webhook configuration

### CORS errors
- Verify CORS_ORIGINS includes your frontend domain
- Must use HTTPS in production

## Performance Tuning

### Current Setup (Good for MVP)
- Single Railway container
- In-memory rate limiting
- Direct database queries

### Scaling (Future)
For traffic > 100 req/sec:
1. Enable Redis for distributed rate limiting:
   ```
   USE_REDIS=true
   REDIS_URL=redis://railway-redis-service:6379
   ```

2. Add caching layer for image listings:
   ```python
   from app.core.cache import cache_control
   @cache_control("public", max_age=300)
   ```

3. Use Railway's auto-scaling:
   - Set min/max replicas
   - Configure CPU/memory limits
   - Enable load balancing

## Security Checklist

- [x] HTTPS enforced via Railway
- [x] Webhook signature verification (X-Signature)
- [x] CORS properly configured
- [x] Rate limiting enabled
- [x] Password hashing with bcrypt
- [x] JWT token validation
- [ ] Add CSRF protection if needed
- [ ] Implement request logging for audit trail
- [ ] Add rate limiting for auth endpoints

## Rollback

If deployment fails:
1. Railway keeps previous versions
2. Go to Railway dashboard → Deployments
3. Click "Redeploy" on previous stable version

## First Deployment Checklist

- [ ] PostgreSQL service created
- [ ] All env variables configured
- [ ] Health check passes
- [ ] Mercado Pago webhook configured
- [ ] Frontend can reach API
- [ ] Test payment flow end-to-end
- [ ] Logs show no errors

## Cost Optimization

Railway pricing:
- **Free tier**: $5/month credit
- **PostgreSQL**: $12/month
- **Container**: Pay-as-you-go (typically $7-15/month for MVP)

Total estimated: ~$20-30/month for production

For cost reduction:
- Use Railway's free tier for development
- Shared database for test environment
- Monitor usage in Railway dashboard
