# ChauFondo Frontend - Deployment Guide

Guía para deployar el frontend de ChauFondo a producción.

## Prerequisitos

- GitHub account con repo clonado
- Vercel o Railway account

## Opción 1: Deploy a Vercel (Recomendado)

### Paso 1: Conectar repo en Vercel

1. Ir a https://vercel.com/new
2. Seleccionar "Import Git Repository"
3. Conectar GitHub account
4. Seleccionar repo `puchiamdp-a11y/ChauFondo`
5. Seleccionar "Project Settings"

### Paso 2: Configurar ambiente

En "Environment Variables" agregar:

```
VITE_API_URL=https://chaufondo-api.up.railway.app
VITE_ENVIRONMENT=production
```

Nota: Reemplazar `https://chaufondo-api.up.railway.app` con URL real del backend en Railway.

### Paso 3: Configurar build

En "Build & Development Settings":

- **Build Command**: Dejar vacío (Vercel auto-detecta)
- **Output Directory**: `frontend` (la raíz del proyecto es frontend/)
- **Install Command**: `npm install` o dejar vacío

### Paso 4: Deploy

1. Click "Deploy"
2. Esperar a que se complete
3. URL en formato: `https://chaufondo-XXXXX.vercel.app`

### Paso 5: Testear

```bash
# Testear landing
curl https://chaufondo-XXXXX.vercel.app

# Verificar assets cargaron
# Abrir DevTools → Network → ver que todos los assets carguen
```

---

## Opción 2: Deploy a Railway

### Paso 1: Crear servicio en Railway

1. Ir a https://railway.app
2. Click "New Project"
3. Seleccionar "Deploy from GitHub"
4. Conectar GitHub y seleccionar repo
5. Click "Deploy"

### Paso 2: Configurar variables

En "Variables":

```
VITE_API_URL=https://chaufondo-api.up.railway.app
VITE_ENVIRONMENT=production
```

### Paso 3: Configurar servicio de frontend

En "Settings" del servicio:

- **Build Command**: Dejar vacío
- **Start Command**: `python3 -m http.server 8080` o `npx http-server`
- **Root Directory**: `frontend`

### Paso 4: Deploy

Railway auto-deploya después de push a main.

---

## Opción 3: Deploy manual a cualquier hosting static

### Estructura

El frontend es un proyecto estático HTML + JS + CSS.

### Paso 1: Preparar archivos

```bash
# Copiar solo los archivos necesarios
cd frontend/
# Archivos necesarios:
# - index.html
# - css/styles.css
# - js/*.js
# - .env.local (o configurar en el servidor)
```

### Paso 2: Upload a servidor web

```bash
# Ejemplo: deploy a cPanel o similar
scp -r frontend/* user@host:/var/www/chaufondo/

# Ejemplo: deploy a AWS S3
aws s3 sync frontend/ s3://mi-bucket/chaufondo/ --delete
```

### Paso 3: Configurar dominio

- Apuntar DNS al servidor
- Configurar SSL/HTTPS

---

## Configuración Post-Deploy

### Backend URL

Verificar que `VITE_API_URL` apunta a la URL correcta:

```javascript
// Si deployment funciona pero los datos no cargan:
// Abrir DevTools → Console → verificar errores CORS
// Los errores indicarán si API_URL es incorrecta
```

### CORS en Backend

El backend DEBE tener configurado CORS para permitir requests desde el frontend:

```python
# En Railway backend, verificar:
CORS_ORIGINS=https://chaufondo-XXXXX.vercel.app,https://chaufondo.app
```

### SSL/HTTPS

Muy importante: El backend DEBE ser HTTPS en producción.

Si hay error "Mixed Content":
- Frontend: HTTPS
- Backend: HTTPS
- Never: Frontend HTTPS + Backend HTTP

---

## Testing Post-Deploy

### 1. Health Check

```bash
# Verificar que frontend carga
curl https://chaufondo-XXXXX.vercel.app/

# Verificar que backend es accesible
curl https://chaufondo-api.up.railway.app/health
```

### 2. Autenticación

1. Abrir frontend en navegador
2. Click "Registrarse"
3. Completar form
4. Verificar en DevTools → Application → Storage
5. Buscar clave `chaufondo_token`
6. Debe haber JWT token

### 3. Upload

1. Login exitoso
2. Arrastra imagen en dashboard
3. Verificar en DevTools → Network
4. Debe ver POST a `/images/upload`
5. Respuesta 200 con JSON

### 4. Historial

1. Upload debe aparecer en grid
2. Botón "Descargar" funciona
3. Botón "Eliminar" funciona

### 5. Pagos

1. Click "Upgrade a Premium"
2. Modal abre con 2 planes
3. Click "Elegir plan"
4. Redirige a Mercado Pago (sandbox en dev)

---

## Troubleshooting

### "Cannot GET /images"

El servidor web no está sirviendo `index.html` para todas las rutas.

Solución: Configurar rewrites (Vercel lo hace automático).

### "CORS error"

Backend no tiene CORS configurado para esta URL.

Solución:
```python
# En backend Railway, agregar:
CORS_ORIGINS=https://chaufondo-XXXXX.vercel.app
```

### "Token inválido en producción"

localStorage puede estar deshabilitado en navegación privada.

Solución: Los usuarios deben abrir en pestañas normales, no privadas.

### "Upload falla con 401"

Token no se está enviando en el header.

Verificar en DevTools → Network → POST /images/upload
Debe haber: `Authorization: Bearer {token}`

### "API timeout"

Backend es muy lento o está caído.

Verificar:
```bash
curl -v https://chaufondo-api.up.railway.app/health
```

---

## Performance

### Optimizaciones implementadas:

- ✅ CSS sin dependencias (inline)
- ✅ JavaScript vanilla (sin bundle)
- ✅ Imágenes lazy-loaded en grid
- ✅ Upload processing simulado (2s)

### Para mejorar aún más:

- Agregar cache headers en servidor
- Comprimir assets (gzip)
- Usar CDN para assets estáticos
- Minificar CSS/JS

---

## Rollback

Si algo sale mal post-deploy:

### Vercel:

1. Ir a "Deployments"
2. Seleccionar deployment anterior
3. Click "Redeploy"

### Railway:

1. Railway auto-rollback en error
2. O volver a hacer push a main con código anterior

---

## Monitoreo

Después de deploy, monitorear:

- Error logs en Vercel/Railway dashboard
- Browser console errors
- Network requests en DevTools
- User feedback sobre velocidad/errores

---

## Checklist Final

Antes de anunciar lanzamiento:

- [ ] Frontend carga sin errores
- [ ] Signup/login funciona
- [ ] Upload anónimo funciona
- [ ] Upload autenticado funciona
- [ ] Historial carga
- [ ] Descarga funciona
- [ ] Eliminación funciona
- [ ] Modal de pagos abre
- [ ] Redirección a Mercado Pago funciona
- [ ] Botones tienen hover effects
- [ ] Responsive en mobile/tablet
- [ ] No hay console errors
- [ ] CORS funciona (sin warnings)
- [ ] SSL/HTTPS funciona

---

## Support

Si hay problemas:

1. Verificar Backend URL en `.env`
2. Abrir DevTools → Network → ver request/response
3. Abrir DevTools → Console → ver errores
4. Verificar backend logs en Railway dashboard
