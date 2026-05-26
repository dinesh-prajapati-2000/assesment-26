# FastAPI Assessment API

REST API built with **FastAPI**, **PostgreSQL**, **Redis**, **SQLAlchemy**, and **Alembic**. Includes JWT authentication, category/product CRUD, pagination, search, and a global error envelope.

## Stack

| Service    | Purpose                          |
|------------|----------------------------------|
| FastAPI    | HTTP API                         |
| PostgreSQL | Primary database                 |
| Redis      | Cache / session-ready connection |
| Alembic    | Database migrations              |

## Quick start (Docker)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Run all services

```bash
docker compose up --build
```

Services:

| Service  | URL / Port              |
|----------|-------------------------|
| API      | http://localhost:8000   |
| Swagger  | http://localhost:8000/docs |
| Postgres | `localhost:5432`        |
| Redis    | `localhost:6379`        |

Migrations run automatically on API startup.

### Stop services

```bash
docker compose down
```

Remove volumes (reset DB):

```bash
docker compose down -v
```

---

## Local development (without Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your DATABASE_URL and REDIS_URL

createdb app_db   # if using local Postgres
alembic upgrade head
uvicorn app.main:app --reload
```

---

## Environment variables

Copy the template and edit values:

```bash
cp .env.example .env
```

| Variable             | Description                          |
|----------------------|--------------------------------------|
| `APP_NAME`           | Application title                    |
| `DEBUG`              | Debug mode (`true` / `false`)        |
| `POSTGRES_USER`      | PostgreSQL username                  |
| `POSTGRES_PASSWORD`  | PostgreSQL password                  |
| `POSTGRES_DB`        | PostgreSQL database name             |
| `POSTGRES_HOST`      | PostgreSQL host (local dev)          |
| `POSTGRES_PORT`      | PostgreSQL port                      |
| `DATABASE_URL`       | Full PostgreSQL connection string    |
| `REDIS_HOST`         | Redis host (local dev)               |
| `REDIS_PORT`         | Redis port                           |
| `REDIS_DB`           | Redis database index                 |
| `REDIS_URL`          | Full Redis connection string         |
| `JWT_SECRET_KEY`     | Secret for signing JWT tokens        |
| `JWT_ALGORITHM`      | JWT algorithm (e.g. `HS256`)         |
| `JWT_EXPIRE_MINUTES` | Token expiry in minutes              |

Docker Compose reads `.env` automatically. Inside containers, `DATABASE_URL` and `REDIS_URL` use Docker service hostnames (`postgres`, `redis`).

---

## API overview

### Public

| Method | Endpoint   | Description        |
|--------|------------|--------------------|
| GET    | `/health`  | Health check (DB + Redis) |
| POST   | `/auth/register` | Register user |
| POST   | `/auth/login`    | Login, get JWT  |

### Protected (Bearer token required)

| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| GET    | `/auth/me`            | Current user                   |
| POST   | `/auth/logout`        | Invalidate token               |
| CRUD   | `/categories`         | Category management            |
| CRUD   | `/products`           | Product management (soft delete) |

### Error response format

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Product not found",
    "details": null
  }
}
```

---

## Sample API calls

Base URL: `http://localhost:8000`

### 1. Health check

```bash
curl -s http://localhost:8000/health | jq
```

**Response:**

```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok"
}
```

---

### 2. Register

```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secret123"
  }' | jq
```

---

### 3. Login (save token)

```bash
export TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secret123"
  }' | jq -r '.access_token')

echo $TOKEN
```

---

### 4. Current user

```bash
curl -s http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### 5. Create category

```bash
curl -s -X POST http://localhost:8000/categories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Electronics"}' | jq
```

---

### 6. List categories (with product count)

```bash
curl -s http://localhost:8000/categories \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### 7. Create product

```bash
curl -s -X POST http://localhost:8000/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category_id": 1,
    "title": "Wireless Mouse",
    "description": "Ergonomic wireless mouse",
    "price": 29.99,
    "stock_quantity": 50,
    "status": "active"
  }' | jq
```

---

### 8. List products (filters, search, pagination)

```bash
curl -s "http://localhost:8000/products?category_id=1&min_price=10&max_price=100&status=active&search=Mouse&sort_by=price&order=asc&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Response shape:**

```json
{
  "items": [...],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "has_next": false
}
```

---

### 9. Get product by ID

```bash
curl -s http://localhost:8000/products/1 \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### 10. Update product

```bash
curl -s -X PUT http://localhost:8000/products/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 24.99,
    "stock_quantity": 45
  }' | jq
```

---

### 11. Soft delete product

```bash
curl -s -X DELETE http://localhost:8000/products/1 \
  -H "Authorization: Bearer $TOKEN" -w "\nHTTP %{http_code}\n"
```

---

### 12. Delete category (409 if products attached)

```bash
curl -s -X DELETE http://localhost:8000/categories/1 \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Example conflict:**

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Cannot delete category with 1 attached product(s)",
    "details": null
  }
}
```

---

### 13. Logout

```bash
curl -s -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer $TOKEN" -w "\nHTTP %{http_code}\n"
```

---

## Project structure

```
├── app/
│   ├── api/routes/       # Route handlers
│   ├── core/             # Config, security, Redis, exceptions
│   ├── db/               # SQLAlchemy session
│   ├── models/           # ORM models
│   └── schemas/          # Pydantic schemas
├── alembic/              # Migrations
├── scripts/entrypoint.sh # Docker startup script
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Database seeding

Seed **10 categories** and **50 products** (5 products per category):

```bash
# Local
python -m scripts.seed

# Re-seed from scratch (clears categories & products)
python -m scripts.seed --fresh

# Docker
docker compose exec api python -m scripts.seed
docker compose exec api python -m scripts.seed --fresh
```

---

## Useful commands

```bash
# View logs
docker compose logs -f api

# Run migrations manually inside API container
docker compose exec api alembic upgrade head

# Open API docs
open http://localhost:8000/docs
```

---

## Validation rules (products)

| Field            | Rule              |
|------------------|-------------------|
| `title`          | 3–200 characters  |
| `description`    | max 500 characters |
| `price`          | must be > 0       |
| `stock_quantity` | integer ≥ 0       |
