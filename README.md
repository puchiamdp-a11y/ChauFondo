# ChauFondo Backend API

Backend MVP para ChauFondo - Servicio de Remoción de Fondo de Imágenes.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **Image Processing**: rembg 2.0.50
- **Deployment**: Railway

## Setup Local (Development)

### 1. Clonar repositorio
```bash
git clone https://github.com/puchiamdp-a11y/chaufondo.git
cd chaufondo
```

### 2. Crear .env desde template
```bash
cp .env.example .env
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

**Opción A: PostgreSQL Local**
```bash
# Crear DB (si no existe)
psql -U postgres -c "CREATE DATABASE chaufondo_db;"

# En .env actualizar:
DATABASE_URL=postgresql://postgres:password@localhost:5432/chaufondo_db

# Ejecutar migrations
alembic upgrade head
```

**Opción B: SQLite (solo desarrollo rápido)**
```bash
# En .env:
DATABASE_URL=sqlite:///./app.db
```

### 5. Ejecutar servidor
```bash
python app/main.py
```

Server estará en: `http://localhost:8000`

## API Endpoints (FASE 1)

### Health Check
```bash
curl http://localhost:8000/health
# Response: {"status": "ok", "db": "connected"}
```

### Root
```bash
curl http://localhost:8000/
# Response: {"message": "Welcome to ChauFondo API", "version": "1.0.0"}
```

## Tests

```bash
# Ejecutar tests
pytest

# Con output verbose
pytest -v

# Con coverage
pytest --cov=app tests/
```

## Project Structure

```
chaufondo/
├── app/
│   ├── core/
│   │   ├── config.py       # Environment config
│   │   ├── database.py     # SQLAlchemy setup
│   │   └── __init__.py
│   ├── auth/               # Auth routes/utils (FASE 2)
│   ├── images/             # Image processing (FASE 3)
│   ├── payments/           # Payment webhooks (FASE 5)
│   ├── models.py           # SQLAlchemy models
│   ├── main.py             # FastAPI app
│   └── __init__.py
├── alembic/                # Database migrations
├── tests/                  # Unit tests
├── requirements.txt        # Python dependencies
├── alembic.ini             # Alembic config
└── .env.example            # Environment template
```

## Database Schema (FASE 1)

### Users Table
- `id` (UUID) - Primary key
- `email` (String) - Unique
- `password_hash` (String)
- `tier` (ENUM: 'free', 'premium')
- `tier_expires_at` (DateTime, nullable)
- `created_at`, `updated_at` (DateTime)

### Images Table
- `id` (UUID)
- `user_id` (FK to Users)
- `original_path` (String)
- `result_path` (String, nullable)
- `status` (ENUM: 'queued', 'processing', 'done', 'failed')
- `processing_time_ms` (Integer, nullable)
- `error_message` (String, nullable)
- `created_at`, `updated_at`

### Payments Table
- `id` (UUID)
- `user_id` (FK to Users)
- `amount` (Float)
- `status` (ENUM: 'pending', 'approved', 'rejected', 'cancelled')
- `mercado_pago_id` (String, unique, nullable)
- `created_at`, `updated_at`

## Migrations

```bash
# Ver estado actual
alembic current

# Ver historial
alembic history

# Crear nueva migration (autogenerate)
alembic revision --autogenerate -m "Description"

# Aplicar migrations
alembic upgrade head

# Revertir última migration
alembic downgrade -1
```

## Next Phases

- **FASE 2 (4-5 días)**: Auth System (Signup, Login, JWT)
- **FASE 3 (5-6 días)**: Upload & Image Processing
- **FASE 4 (3-4 días)**: Rate Limiting & Tier System
- **FASE 5 (4-5 días)**: Payments (Mercado Pago)
- **FASE 6 (3-4 días)**: Testing, Deployment & Monitoring

## Documentation

- API endpoints: `API.md` (después de FASE 2)
- Deployment: `DEPLOYMENT.md` (FASE 6)

## Contributors

- Backend development with Claude Code

---

**Status**: FASE 1 (Setup + Database Schema) - Ready ✅
