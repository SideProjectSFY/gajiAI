# Story 0.5: Docker Configuration & Inter-Service Communication

**Epic**: Epic 0 - Project Setup & Infrastructure  
**Priority**: P0 - Critical  
**Status**: Not Started  
**Estimated Effort**: 8 hours

## Description

Create Docker Compose configuration for all services implementing **Pattern B architecture**: Spring Boot (API Gateway, port 8080), FastAPI (internal-only, port 8000), PostgreSQL (metadata), ChromaDB (VectorDB dev), Redis (Celery), and Vue.js/Nginx (frontend, port 3000).

## Dependencies

**Blocks**:

- Story 0.6: Inter-Service Health Check (needs Docker network)
- All development and deployment workflows

**Requires**:

- Story 0.1: Spring Boot Backend Setup (API Gateway)
- Story 0.2: FastAPI AI Service Setup (internal-only)
- Story 0.3: PostgreSQL Database Setup (metadata only)
- Story 0.4: Vue.js Frontend Project Setup

## Acceptance Criteria

- [ ] `docker-compose.yml` defines **6 services**: postgres, redis, chromadb, backend, ai-service, frontend
- [ ] Custom Docker network `gaji-network` for inter-service communication
- [ ] **PostgreSQL** volume persistence: `postgres-data:/var/lib/postgresql/data`
- [ ] **ChromaDB** volume persistence: `chromadb-data:/chroma/chroma` (VectorDB for dev)
- [ ] **Redis** for Celery task queue (novel ingestion, character extraction)
- [ ] Environment variables managed via `.env` file (not hardcoded in compose)
- [ ] **Spring Boot** (API Gateway) accessible at `http://localhost:8080`
- [ ] **FastAPI** (internal-only) accessible at `http://ai-service:8000` (Docker network ONLY)
- [ ] **ChromaDB** accessible at `http://localhost:8001` (dev only)
- [ ] **Vue.js/Nginx** accessible at `http://localhost:3000`
- [ ] **PostgreSQL** accessible at `localhost:5432`
- [ ] **Redis** accessible at `localhost:6379`
- [ ] Health check probes configured for all services
- [ ] Services start in correct order with `depends_on` conditions
- [ ] Hot reload enabled for development:
  - Backend: Spring DevTools
  - AI Service: uvicorn --reload
  - Frontend: Vite HMR
- [ ] `docker-compose up` brings up entire stack in < 3 minutes
- [ ] **FastAPI NOT exposed externally** (Pattern B: internal network only)

## Technical Notes

**docker-compose.yml Structure**:

```yaml
version: "3.8"

networks:
  gaji-network:
    driver: bridge

volumes:
  postgres-data:
  chromadb-data:
  redis-data:

services:
  # PostgreSQL - Metadata storage only (13 tables)
  postgres:
    image: postgres:15-alpine
    container_name: gaji-postgres
    environment:
      POSTGRES_DB: ${DB_NAME:-gaji_db}
      POSTGRES_USER: ${DB_USER:-gaji_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - gaji-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-gaji_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis - Celery broker + Long Polling task storage (600s TTL)
  redis:
    image: redis:7-alpine
    container_name: gaji-redis
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    networks:
      - gaji-network
    command: redis-server --appendonly yes # AOF persistence
    mem_limit: 512m # Redis memory limit
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ChromaDB - VectorDB for development (768-dim embeddings, 5 collections)
  chromadb:
    image: chromadb/chroma:0.4.18
    container_name: gaji-chromadb
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
    volumes:
      - chromadb-data:/chroma/chroma
    ports:
      - "8001:8000" # Expose on 8001 to avoid conflict with FastAPI
    networks:
      - gaji-network
    mem_limit: 4g # ChromaDB memory limit
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Spring Boot - API Gateway (Pattern B)
  backend:
    build:
      context: ./core-backend
      dockerfile: Dockerfile.dev
    container_name: gaji-backend
    environment:
      # PostgreSQL (metadata only)
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/${DB_NAME:-gaji_db}
      SPRING_DATASOURCE_USERNAME: ${DB_USER:-gaji_user}
      SPRING_DATASOURCE_PASSWORD: ${DB_PASSWORD}
      # FastAPI internal URL (Pattern B)
      FASTAPI_BASE_URL: http://ai-service:8000
      # Gemini API key (used by FastAPI, passed for config validation)
      GEMINI_API_KEY: ${GEMINI_API_KEY}
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - gaji-network
    volumes:
      - ./core-backend:/app
      - /app/build # Exclude build directory
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # FastAPI - Internal-only AI service (Pattern B)
  ai-service:
    build:
      context: ./ai-backend
      dockerfile: Dockerfile.dev
    container_name: gaji-ai-service
    environment:
      # Gemini API
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      # VectorDB
      VECTORDB_TYPE: chromadb
      CHROMADB_HOST: chromadb
      CHROMADB_PORT: 8000
      # Spring Boot URL (for callbacks)
      SPRING_BOOT_URL: http://backend:8080
      # Redis for Celery + Long Polling (600s TTL)
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
    # NO ports exposed externally (Pattern B: internal network only)
    expose:
      - "8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_healthy
    networks:
      - gaji-network
    volumes:
      - ./ai-backend:/app
    command: >
      sh -c "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
             celery -A app.celery_app worker --loglevel=info"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Vue.js Frontend (Pattern B: talks to Spring Boot only)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: gaji-frontend
    environment:
      # Pattern B: Frontend → Spring Boot ONLY
      VITE_API_BASE_URL: http://localhost:8080/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - gaji-network
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/styled-system # Panda CSS generated files
    command: pnpm dev --host 0.0.0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Service-to-Service Communication (Pattern B)**:

- **Frontend → Backend**: `http://localhost:8080/api/v1` (external, via host)
- **Backend → FastAPI**: `http://ai-service:8000/api` (internal network ONLY)
- **FastAPI → ChromaDB**: `http://chromadb:8000/api/v1` (internal network)
- **FastAPI → Spring Boot**: `http://backend:8080/api/internal` (callbacks)
- **Backend → PostgreSQL**: `jdbc:postgresql://postgres:5432/gaji_db`
- **Celery → Redis**: `redis://redis:6379/0`

**Environment Variables (.env file)**:

```env
# Database
DB_NAME=gaji_db
DB_USER=gaji_user
DB_PASSWORD=your_secure_password

# Gemini API (Pattern B: only FastAPI uses it)
GEMINI_API_KEY=your_gemini_api_key

# VectorDB (dev uses ChromaDB, prod uses Pinecone)
VECTORDB_TYPE=chromadb
```

**Why FastAPI is NOT Exposed Externally**:

- **Pattern B**: Frontend → Spring Boot → FastAPI (internal proxy)
- **Security**: Gemini API key never exposed to browser
- **Simplicity**: Single authentication flow
- **Cost**: No need for separate SSL certificate

**Dockerfile.dev Examples**:

**Spring Boot (core-backend/Dockerfile.dev)**:

```dockerfile
FROM eclipse-temurin:17-jdk-alpine
WORKDIR /app
COPY build.gradle settings.gradle gradlew ./
COPY gradle ./gradle
RUN ./gradlew dependencies --no-daemon
COPY src ./src
CMD ["./gradlew", "bootRun", "--no-daemon"]
```

**FastAPI (ai-backend/Dockerfile.dev)**:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt
COPY . .
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload & celery -A app.celery_app worker --loglevel=info"]
```

**Frontend (frontend/Dockerfile.dev)**:

```dockerfile
FROM node:20-alpine
WORKDIR /app
RUN npm install -g pnpm
COPY package.json pnpm-lock.yaml ./
RUN pnpm install
COPY . .
RUN pnpm prepare  # Generate Panda CSS
CMD ["pnpm", "dev", "--host", "0.0.0.0"]
```

## QA Checklist

### Functional Testing

- [ ] `docker-compose up` starts all 6 services successfully
- [ ] All services reach healthy state within 3 minutes
- [ ] PostgreSQL accessible at `localhost:5432`
- [ ] Redis accessible at `localhost:6379`
- [ ] ChromaDB accessible at `http://localhost:8001`
- [ ] Spring Boot API Gateway accessible at `http://localhost:8080`
- [ ] **FastAPI NOT accessible from host** (internal network only)
- [ ] Frontend accessible at `http://localhost:3000`
- [ ] `docker-compose down` stops all services cleanly
- [ ] `docker-compose down -v` removes all volumes

### Pattern B Architecture Validation

- [ ] Frontend can reach Spring Boot at `http://localhost:8080/api/v1`
- [ ] **Frontend CANNOT reach FastAPI directly** (no port exposed)
- [ ] Spring Boot can proxy requests to FastAPI at `http://ai-service:8000`
- [ ] FastAPI can callback to Spring Boot at `http://backend:8080/api/internal`
- [ ] Test AI request flow: Frontend → Spring Boot → FastAPI → Gemini API

### Service Health Checks

- [ ] PostgreSQL health check passes: `pg_isready`
- [ ] Redis health check passes: `redis-cli ping`
- [ ] ChromaDB health check passes: `/api/v1/heartbeat`
- [ ] Spring Boot health check passes: `/actuator/health` includes FastAPI status
- [ ] FastAPI health check passes: `/health` includes Gemini + ChromaDB status
- [ ] Frontend health check passes: responds to `curl`

### Volume Persistence

- [ ] PostgreSQL data persists after `docker-compose down`
- [ ] ChromaDB data persists after restart
- [ ] Novel ingestion data survives container restart
- [ ] `docker-compose down -v` removes all persisted data

### Hot Reload Development

- [ ] Spring Boot auto-reloads on Java file changes (DevTools)
- [ ] FastAPI auto-reloads on Python file changes (uvicorn --reload)
- [ ] Frontend auto-reloads on Vue file changes (Vite HMR)
- [ ] Panda CSS regenerates on style changes

### Environment Variables

- [ ] `.env` file loaded correctly
- [ ] `GEMINI_API_KEY` passed to FastAPI (not exposed to frontend)
- [ ] `DB_PASSWORD` not logged or exposed
- [ ] Missing `GEMINI_API_KEY` causes FastAPI to fail with clear error message

### Service Dependencies

- [ ] Backend waits for PostgreSQL to be healthy before starting
- [ ] AI Service waits for PostgreSQL, Redis, ChromaDB before starting
- [ ] Frontend waits for Backend before starting
- [ ] Services start in correct order: postgres/redis/chromadb → backend/ai-service → frontend

### Network Communication

- [ ] Services can communicate via `gaji-network`
- [ ] DNS resolution works (e.g., `backend` resolves to backend container IP)
- [ ] No network conflicts (all ports unique)

### Security

- [ ] **FastAPI not exposed externally** (Pattern B security benefit)
- [ ] Gemini API key not visible in frontend network requests
- [ ] PostgreSQL password not hardcoded in docker-compose.yml
- [ ] Docker network isolated from host network (except exposed ports)

### Performance

- [ ] Full stack startup time < 3 minutes
- [ ] Health check overhead < 50ms per service
- [ ] Hot reload latency < 2 seconds

## Estimated Effort

8 hours

### Functional Testing

- [ ] `docker-compose up` starts all 4 services successfully
- [ ] PostgreSQL data persists after `docker-compose down`
- [ ] Services communicate via Docker network (test backend→ai-service call)
- [ ] Environment variables loaded from .env file
- [ ] Services restart automatically on failure

### Health Checks

- [ ] All health check endpoints return 200 status
- [ ] `depends_on` waits for PostgreSQL healthy before starting backend
- [ ] Unhealthy service triggers automatic restart
- [ ] `docker-compose ps` shows all services as "healthy"

### Development Experience

- [ ] Code changes in backend trigger Spring DevTools reload
- [ ] Code changes in frontend trigger Vite HMR (< 2s)
- [ ] `docker-compose logs -f backend` shows real-time logs
- [ ] Volume mounts work for all services

### Performance

- [ ] Full stack startup < 2 minutes on first run
- [ ] Subsequent starts < 30 seconds (cached images)
- [ ] No resource leaks (memory stable after 1 hour)

### Configuration

- [ ] .env.example includes all required variables
- [ ] No secrets hardcoded in docker-compose.yml
- [ ] Port conflicts detected and reported clearly

## Estimated Effort

8 hours
