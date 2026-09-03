# ChauFondo Frontend

Frontend minimalista para ChauFondo - Eliminador de fondos automático SaaS.

## Stack

- **HTML5** - Markup semántico
- **Vanilla JavaScript** - Sin dependencias
- **CSS3** - Estilos puro
- **Fetch API** - Llamadas HTTP

## Estructura

```
frontend/
├── index.html          # Archivo HTML principal
├── css/
│   └── styles.css      # Estilos globales
├── js/
│   ├── config.js       # Configuración
│   ├── api.js          # Cliente HTTP
│   ├── auth.js         # Autenticación (signup/login)
│   ├── upload.js       # Lógica de upload
│   ├── payment.js      # Integración Mercado Pago
│   └── ui.js           # Gestión de UI
├── .env.example        # Template de variables
└── README.md           # Este archivo
```

## Instalación

### Requisitos
- Node.js 16+ (opcional, solo para development server)
- Acceso a backend en Railway

### Setup

1. Clonar repositorio
```bash
git clone <repo>
cd frontend
```

2. Configurar variables de entorno
```bash
cp .env.example .env.local
# Editar .env.local con URL real del backend
```

3. Abrir en navegador
```bash
# Option 1: Abrir directamente
open index.html

# Option 2: Servidor local (Python)
python3 -m http.server 8080

# Option 3: Servidor local (Node)
npx http-server
```

Visitar `http://localhost:8080`

## API Endpoints

### Públicos (sin auth)

```
POST /auth/signup
POST /auth/login
POST /images/upload
GET /health
```

### Protegidos (Bearer token)

```
GET /auth/me
GET /images
DELETE /images/{id}
POST /payment/create-subscription
```

## Flujos

### 1. Upload Anónimo
1. Usuario arrastra imagen
2. POST /images/upload (sin token)
3. Backend retorna PNG binario
4. Browser descarga automáticamente
5. Mostrar popup: "Crear cuenta"

### 2. Autenticación
1. Click "Registrarse"
2. Completar email + password
3. POST /auth/signup
4. Guardar token en localStorage
5. Redirigir a dashboard

### 3. Upload Autenticado
1. Usuario autenticado arrastra imagen
2. POST /images/upload (con Bearer token)
3. Backend retorna { image_id, processed_url }
4. Mostrar preview
5. Agregar a historial

### 4. Upgrade Premium
1. Click "Upgrade Premium"
2. POST /payment/create-subscription
3. Redirigir a Mercado Pago (init_point)
4. Usuario paga
5. Webhook actualiza tier
6. Al volver, mostrar "Premium activo"

## Configuración

### Config.js

Variables globales:
- `CONFIG.API_URL` - URL del backend
- `CONFIG.TOKEN_KEY` - Clave para localStorage
- `CONFIG.RATE_LIMITS` - Límites por tier

### Variables de entorno

```env
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development
```

En producción:
```env
VITE_API_URL=https://chaufondo-api.up.railway.app
VITE_ENVIRONMENT=production
```

## Autenticación

Token JWT guardado en localStorage con key `chaufondo_token`

```javascript
// Obtener token
const token = getAuthToken();

// Guardar token
setAuthToken(token);

// Verificar autenticación
if (isAuthenticated()) { ... }
```

## Rate Limiting

Límites por tier:
- **Anónimo**: 50 uploads/día (por IP)
- **Free**: 5 uploads/día (por user_id)
- **Premium**: 1000 uploads/mes

Contador guardado en localStorage, se reset cada día.

## Desarrollo

### Agregar nuevo endpoint

1. Agregar método a `APIClient` en `api.js`
```javascript
async myEndpoint(data) {
  const response = await this.request('/my-endpoint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return response.data;
}
```

2. Usar en módulos
```javascript
await api.myEndpoint(data);
```

### Agregar nueva página

1. Agregar `<div data-page="pageName">` en HTML
2. Agregar método a `UIManager` en `ui.js`
```javascript
navigateToPage('pageName');
```

## Deploy

### A Vercel

```bash
# 1. Push a Git
git push

# 2. Vercel auto-deploya
# No necesita build step

# 3. Configurar variables de entorno en Vercel dashboard
VITE_API_URL=https://chaufondo-api.up.railway.app
```

### A Railway

```bash
# 1. Conectar repo
# 2. Configurar build: None
# 3. Start command: `python3 -m http.server 8080`
# 4. Set variables en dashboard
```

### A cualquier static host

```bash
# Solo copiar archivos a servidor web
scp -r frontend/* user@host:/var/www/chaufondo/
```

## Troubleshooting

### "CORS error"
Asegurar que backend tiene `CORS_ORIGINS` configurado para incluir URL del frontend.

### "Token inválido"
Limpiar localStorage: `localStorage.clear()` y reloguarse.

### "Upload no funciona"
1. Verificar API_URL en config.js
2. Verificar token en Developer Tools → Application → Storage
3. Verificar CORS headers en Network tab

## Notas

- Vanilla JS para máxima compatibilidad
- CSS puro, sin preprocessadores
- Código borrable y fácil de mantener
- Sin emojis ni "vibes"
- Profesional y limpio

## Licencia

© 2025 ChauFondo. Todos los derechos reservados.
