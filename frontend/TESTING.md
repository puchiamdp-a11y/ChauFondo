# ChauFondo Frontend - Testing Guide

Guía completa para testear todas las funcionalidades del frontend.

## Setup para Testing Local

### Requisitos

- Backend corriendo en `http://localhost:8000`
- Frontend en `http://localhost:8080`
- Terminal con curl o Postman

### Iniciar

```bash
# Terminal 1: Backend (desde raíz del repo)
cd app && python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
python3 -m http.server 8080
# o
npx http-server
```

Visitar `http://localhost:8080`

---

## Test 1: Upload Anónimo

### Flujo

1. En landing, ver "Carga una imagen"
2. Arrastra imagen (JPG, PNG, WEBP)
3. Ver estado "Procesando imagen..."
4. Esperar 2 segundos
5. Ver PNG descargado automáticamente

### Verificar

```javascript
// En DevTools Console:
// 1. Ver request POST a /images/upload
// 2. Response debe ser image/png (blob)
// 3. No debe llevar token en header

// Network tab:
// POST /images/upload → 200 OK
// Response size: tamaño del PNG
```

### Validaciones

- ✅ Arrastra archivo funciona
- ✅ Validación de tipo (rechazar .gif)
- ✅ Validación de tamaño (rechazar >25 MB)
- ✅ Download automático
- ✅ Rate limit: después de 50 uploads debe fallar

### Contador de rate limit

```javascript
// En Console:
upload.uploadCount  // debe incrementar
upload.getRemainingUploads()  // debe disminuir

// Resetea diariamente (stored en localStorage)
localStorage.getItem('uploadCount')  // {"date": "...", "count": 50}
```

---

## Test 2: Autenticación

### Test 2a: Signup

1. Click "Registrarse"
2. Llena form:
   - Email: `test@example.com`
   - Password: `password123`
3. Click "Registrarse"

### Verificar

```javascript
// En DevTools → Network:
// POST /auth/signup
// Request body: {"email": "test@example.com", "password": "password123"}
// Response: {"access_token": "eyJ...", "token_type": "bearer"}

// En DevTools → Application → Local Storage:
// Buscar clave: chaufondo_token
// Valor: debe ser JWT token

// Verificar token:
const token = localStorage.getItem('chaufondo_token');
console.log(token);  // eyJ...
```

### Validaciones

- ✅ Email válido (rechaza emails inválidos)
- ✅ Password mínimo 8 caracteres
- ✅ Token guardado en localStorage
- ✅ Redirige a dashboard después de signup

### Test 2b: Login

1. En landing, logout si ya hay sesión
2. Click "Inicia sesión"
3. Completa form con credenciales anteriores
4. Click "Inicia sesión"

### Verificar

```javascript
// Similar a signup pero:
// POST /auth/login
// Response: {"access_token": "...", "token_type": "bearer"}

// Verificar que redirige a dashboard
// Debe ver email en header
```

### Test 2c: Logout

1. En dashboard, click "Cerrar sesión"
2. Redirige a landing
3. localStorage debe estar limpio

```javascript
// En Console:
localStorage.getItem('chaufondo_token')  // null
auth.isLoggedIn()  // false
```

---

## Test 3: Dashboard Upload

### Flujo

1. Estar autenticado (hacer login)
2. En dashboard, arrastra imagen
3. Procesando...
4. Ver preview de imagen procesada
5. Ver imagen en grid

### Verificar

```javascript
// En Network tab:
// POST /images/upload
// Request: FormData con file
// Response: {"id": "uuid", "original_url": "...", "processed_url": "...", "created_at": "..."}

// En HTML:
// Grid debe mostrar la imagen con botones: Descargar, Eliminar
```

### Contador actualiza

```javascript
// En Dashboard header, "X / 5 usos diarios" debe actualizar
// Inicial: "0 / 5"
// Después de upload: "1 / 5"
```

### Almacenamiento

```javascript
// En Database (verificar en Railway):
// Tabla: images
// Debe tener nuevo row con:
// - user_id: del usuario autenticado
// - original_url: URL guardada
// - processed_url: URL del PNG procesado
// - created_at: timestamp
```

---

## Test 4: Historial de Imágenes

### Flujo

1. Estar autenticado
2. Sube 2-3 imágenes
3. Grid debe mostrar todas

### Verificar

```javascript
// En Network tab:
// GET /images (cuando abre dashboard)
// Response: array de imágenes

// Contar cards en grid:
document.querySelectorAll('.image-card').length  // debe ser 2-3
```

### Test 4a: Descargar Imagen

1. Click botón "Descargar" en una imagen
2. PNG debe descargar

```javascript
// En Network tab:
// Debe haber GET a imagen URL
// O download directo del blob
```

### Test 4b: Eliminar Imagen

1. Click botón "Eliminar"
2. Confirmar diálogo
3. Imagen desaparece del grid

```javascript
// En Network tab:
// DELETE /images/{imageId}
// Response: 200 OK

// Grid actualiza automáticamente
// Menos cards que antes
```

---

## Test 5: Rate Limiting

### Test 5a: Anónimo (50/día)

```bash
# Simular 50 uploads
for i in {1..50}; do
  # Arrastra imagen en landing
  # Después del 50vo debe fallar
done
```

Esperado:
- Uploads 1-50: ✅ Funcionan
- Upload 51: ❌ Error "Límite diario alcanzado (50 uploads)"

```javascript
// Verificar contador:
upload.uploadCount  // 50
upload.canUpload()  // false
```

### Test 5b: Free user (5/día)

```bash
# Después de autenticarse como free
# Sube 5 imágenes
# La 6ta debe fallar
```

Esperado:
- Dashboard: "5 / 5 usos diarios"
- Upload 6: ❌ Error "Límite diario alcanzado (5 uploads)"

### Test 5c: Premium (ilimitado)

```bash
# Upgrade a premium
# Sube 10+ imágenes
# Todas deben funcionar
```

Esperado:
- Dashboard: "10 / 1000 usos"
- Todos uploads exitosos

---

## Test 6: Pagos (Mercado Pago)

### Flujo

1. Free user en dashboard
2. Click "Upgrade a Premium"
3. Modal abre con 2 planes

### Verificar Modal

```javascript
// Estructura:
// - Título: "Upgrade a Premium"
// - 2 cards: mes y año
// - Cada card tiene:
//   - Nombre del plan
//   - Precio
//   - Badge "Ahorra 58%" (solo en año)
//   - Lista de features
//   - Botón "Elegir plan"

document.querySelectorAll('.plan-card').length  // 2
```

### Test 6a: Plan Mensual

1. Click "Elegir plan" en Premium - 1 Mes
2. Verificar request

```javascript
// En Network tab:
// POST /payment/create-subscription
// Request body: {"plan": "premium_month"}
// Response: {"id": "...", "init_point": "https://mercadopago.com/checkout/..."}

// Debe redirigir a Mercado Pago (sandbox en dev)
```

### Test 6b: Plan Anual

1. Click "Elegir plan" en Premium - 1 Año
2. Verificar request

```javascript
// POST /payment/create-subscription
// Request body: {"plan": "premium_year"}
// Response: {"id": "...", "init_point": "https://..."}

// Redirect a Mercado Pago
```

### Sandbox vs Producción

En desarrollo:
- Mercado Pago usa SANDBOX
- Usar tarjeta de prueba: `4111 1111 1111 1111`
- Mes: 01, Año: 25, CVV: 123

En producción:
- Mercado Pago usa producción real
- Solo tarjetas reales funcionan

---

## Test 7: Tier Display

### Test 7a: Free User

```javascript
// En dashboard:
// Document: <span class="user-tier">Free</span>

// Clase: user-tier (azul)
// NO debe mostrar días

document.getElementById('userTier').textContent  // "Free"
```

### Test 7b: Premium User

```javascript
// Después de upgrade:
// <span class="user-tier premium">Premium (30 días)</span>

// Clase: user-tier premium (dorado)
// Debe mostrar días restantes

document.getElementById('userTier').textContent  // "Premium (30 días)"
document.getElementById('userTier').className  // "user-tier premium"
```

---

## Test 8: Error Handling

### Test 8a: Backend Offline

1. Apagar backend
2. Intentar login en frontend
3. Debe mostrar error

Esperado:
```
❌ Error de conexión - Verifica tu internet
o
❌ El servidor no responde
```

### Test 8b: Invalid Credentials

1. Login con email/password incorrectos

Esperado:
```
❌ (mensaje del backend, ej: "Invalid credentials")
```

### Test 8c: File Too Large

1. Intentar subir archivo >25 MB

Esperado:
```
❌ El archivo no puede superar 25 MB
```

### Test 8d: Invalid File Type

1. Intentar subir .gif o .bmp

Esperado:
```
❌ Solo se permiten JPG, PNG o WEBP
```

---

## Test 9: Responsive Design

### Desktop (1200px+)

```
✓ Landing: hero + upload + features
✓ Dashboard: 2-3 imágenes por fila
✓ Modal: 2 planes lado a lado
```

### Tablet (768px)

```
✓ Hero: reducido pero legible
✓ Grid: 2 imágenes por fila
✓ Modal: 1 plan por fila
✓ Upload area: responsive
```

### Mobile (380px)

```
✓ Hero: ajustado a viewport
✓ Grid: 1 imagen por fila
✓ Modal: 1 plan, stack vertical
✓ Buttons: full-width
✓ Form: inputs legibles
```

---

## Test 10: localStorage & Session

### Persistencia

1. Hacer login
2. Recargar página (F5)
3. Debe estar en dashboard (token persiste)

### Reset

1. Clear localStorage
2. Recargar página
3. Debe ir a landing

```javascript
// Limpiar:
localStorage.clear()

// O específico:
localStorage.removeItem('chaufondo_token')
localStorage.removeItem('uploadCount')
```

---

## Checklist de Testing

```
Landing Page:
☐ Upload anónimo funciona
☐ Validación de archivos
☐ Rate limit 50/día
☐ Descarga PNG automática
☐ Link "Registrarse" funciona

Auth:
☐ Signup crea cuenta
☐ Validación de email
☐ Validación de password
☐ Token guardado
☐ Login funciona
☐ Logout limpia datos

Dashboard:
☐ Email visible en header
☐ Tier display correcto
☐ Upload guarda en DB
☐ Grid carga imágenes
☐ Botón descargar funciona
☐ Botón eliminar funciona
☐ Contador actualiza

Pagos:
☐ Modal abre
☐ 2 planes muestran
☐ Redirige a Mercado Pago
☐ Tier actualiza post-pago

Errors:
☐ Backend offline → error visible
☐ Archivo grande → error visible
☐ Archivo inválido → error visible
☐ Rate limit → error visible

Responsive:
☐ Desktop funciona
☐ Tablet funciona
☐ Mobile funciona

Performance:
☐ No errores en console
☐ Network requests exitosas
☐ Tiempo de carga aceptable
```

---

## Debug Tips

### Ver logs

```javascript
// En Console:
CONFIG.API_DEBUG = true  // Activar logs

// Luego verás:
// [API] POST /auth/login - 200 OK
// [API] GET /images - 200 OK
```

### Ver estado del auth

```javascript
// En Console:
auth.getUser()  // {id, email, tier, ...}
auth.isLoggedIn()  // true/false
auth.isPremium()  // true/false

// Estado del upload
upload.uploadCount  // número
upload.getRateLimit()  // número
upload.getRemainingUploads()  // número
```

### Ver requests en Network

1. Abrir DevTools → Network
2. Ejecutar acción (login, upload, etc)
3. Ver request/response headers
4. Verificar: Authorization header, status code, body

### Simular errores

```javascript
// Forzar error de autenticación
clearAuthToken()

// Forzar error en upload
// Cambiar API_URL a endpoint inválido
CONFIG.API_URL = 'http://invalid'
```

---

## Datos de Test

### Usuario de prueba

```
Email: test@example.com
Password: password123
```

### Imágenes de prueba

Usar cualquier PNG/JPG menor a 25 MB.

O descargar:
- https://www.sample-videos.com/png
- https://loremflickr.com/200/200/people

---

## Reporte de Errores

Si encuentras un bug:

1. Reproducir el problema
2. Tomar screenshot/video
3. Ver DevTools → Console (copiar error)
4. Ver DevTools → Network (copiar request/response)
5. Reportar en GitHub issues con detalles
