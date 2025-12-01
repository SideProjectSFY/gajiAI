# Development Setup Guide

**Project**: Gaji - Interactive Fiction Platform  
**Last Updated**: 2025-11-14  
**Target**: Local Development Environment  
**Architecture**: Hybrid Database (PostgreSQL + VectorDB)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Repository Setup](#repository-setup)
3. [Backend Setup](#backend-setup)
4. [AI Backend Setup](#ai-backend-setup)
5. [Database Setup](#database-setup)
6. [VectorDB Setup](#vectordb-setup)
7. [Frontend Setup](#frontend-setup)
8. [Docker Setup](#docker-setup)
9. [Environment Variables](#environment-variables)
10. [Running the Full Stack](#running-the-full-stack)
11. [Verification](#verification)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software           | Version | Purpose                    |
| ------------------ | ------- | -------------------------- |
| **Java JDK**       | 17+     | Core Backend (Spring Boot) |
| **Gradle**         | 8.x     | Java build tool            |
| **Python**         | 3.11+   | AI Backend (FastAPI)       |
| **uv**             | Latest  | Python package manager     |
| **Node.js**        | 18+     | Frontend build             |
| **pnpm**           | 8+      | Node package manager       |
| **PostgreSQL**     | 15.x    | Metadata database          |
| **ChromaDB**       | Latest  | VectorDB (development)     |
| **Redis**          | 7+      | Celery message broker      |
| **Docker**         | 24+     | Container orchestration    |
| **Docker Compose** | 2.x     | Multi-container setup      |

### Installation Commands

**macOS (Homebrew)**:

```bash
# Java 17
brew install openjdk@17
echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"' >> ~/.zshrc

# Python 3.11
brew install python@3.11
pip install uv

# Node.js & pnpm
brew install node
npm install -g pnpm

# PostgreSQL
brew install postgresql@15
brew services start postgresql@15

# Redis
brew install redis
brew services start redis

# Docker
brew install --cask docker
```

**Windows (Chocolatey/Scoop)**:

```powershell
# Java 17
scoop install openjdk17

# Python 3.11
scoop install python311
pip install uv

# Node.js & pnpm
scoop install nodejs
npm install -g pnpm

# PostgreSQL
scoop install postgresql15

# Redis (via Docker recommended)
docker pull redis:7-alpine

# Docker Desktop
scoop install docker
```

**Verification**:

```bash
java -version        # Should show 17.x
python3 --version    # Should show 3.11.x
node -v              # Should show v18.x
pnpm -v              # Should show 8.x
psql --version       # Should show 15.x
redis-cli --version  # Should show 7.x
docker --version     # Should show 24.x
```

---

## Repository Setup

### Multirepo Structure

Gaji uses **separate repositories** for each service:

```bash
# Clone all repositories
git clone https://github.com/your-org/gaji-core-backend.git
git clone https://github.com/your-org/gaji-ai-backend.git
git clone https://github.com/your-org/gaji-frontend.git
git clone https://github.com/your-org/gaji-api-contracts.git

# Organize workspace
mkdir gaji-workspace
cd gaji-workspace
mv ../gaji-core-backend ./core-backend
mv ../gaji-ai-backend ./ai-backend
mv ../gaji-frontend ./frontend
mv ../gaji-api-contracts ./api-contracts
```

### Repository Structure

```
gaji-workspace/
├── core-backend/          # Repository 1: Spring Boot
│   ├── src/main/java/
│   ├── src/main/resources/
│   ├── build.gradle
│   └── Dockerfile
│
├── ai-backend/            # Repository 2: FastAPI
│   ├── app/
│   │   ├── api/
│   │   └── services/
│   ├── chroma_data/       # ChromaDB persistent storage
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/              # Repository 3: Vue.js
│   ├── src/
│   ├── package.json
│   └── Dockerfile
│
├── api-contracts/         # Repository 4: Shared OpenAPI specs
│   ├── openapi.yaml
│   └── README.md
│
└── docker-compose.yml     # Optional: Shared docker-compose for local dev
```

**Benefits**:

- Independent deployment cycles per service
- Clear ownership boundaries
- Easier CI/CD configuration
- Better suited for team growth

---

## Backend Setup

**Story Reference**: Epic 0, Story 0.1 - Spring Boot Backend Setup

### 1. Navigate to Backend Directory

```bash
cd gaji-workspace/core-backend
```

### 2. Configure Environment

Create `core-backend/.env`:

```properties
# Server Configuration
SERVER_PORT=8080
SPRING_PROFILES_ACTIVE=local

# Database Configuration
SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/gaji
SPRING_DATASOURCE_USERNAME=gaji_user
SPRING_DATASOURCE_PASSWORD=your_password_here

# JWT Configuration
JWT_SECRET=your-256-bit-secret-key-here-minimum-32-characters
JWT_ACCESS_TOKEN_EXPIRATION=3600000   # 1 hour in ms
JWT_REFRESH_TOKEN_EXPIRATION=604800000 # 7 days in ms

# AI Backend URL
AI_BACKEND_URL=http://localhost:8000

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### 3. Build & Run

```bash
# Build project
./gradlew clean build

# Run with Spring Boot
./gradlew bootRun

# Or run JAR directly
java -jar build/libs/gaji-backend-0.0.1-SNAPSHOT.jar
```

### 4. Verify Backend

```bash
# Health check
curl http://localhost:8080/actuator/health

# Expected response:
# {"status":"UP"}
```

**Default Port**: 8080

---

## AI Backend Setup

**Story Reference**: Epic 0, Story 0.2 - FastAPI AI Backend Setup

### 1. Navigate to AI Backend Directory

```bash
cd gaji-workspace/ai-backend
```

### 2. Create Virtual Environment

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # macOS/Linux

# Or using standard venv
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Using uv (faster)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

**Key Dependencies**:

- `fastapi[all]==0.104.1`
- `langchain==0.0.335`
- `chromadb==0.4.18`
- `uvicorn[standard]==0.24.0`
- `llama-cpp-python` or `transformers` (for local LLM inference)

### 4. Configure Environment

Create `ai-backend/.env`:

```properties
# Server Configuration
PORT=8000
ENV=development

# Local LLM Configuration
LLM_MODEL_PATH=/path/to/your/llm/model  # e.g., Llama-2-7b, Mistral-7B
LLM_MODEL_TYPE=llama  # llama, mistral, or other supported types
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.7
LLM_CONTEXT_LENGTH=4096

# Vector Store Configuration
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
CHROMADB_COLLECTION_NAME=gaji_books

# Core Backend URL
CORE_BACKEND_URL=http://localhost:8080
```

### 5. Run FastAPI Server

```bash
# Development mode with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. Verify AI Backend

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2025-11-13T..."}

# API docs (Swagger UI)
open http://localhost:8000/docs
```

**Default Port**: 8000

---

## Database Setup

**Story Reference**: Epic 0, Story 0.3 - PostgreSQL Database Setup

### 1. Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE gaji;
CREATE USER gaji_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE gaji TO gaji_user;

# Enable required extensions (NO pgvector - using VectorDB instead)
\c gaji
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  # For trigram search

\q
```

### 2. Run Flyway Migrations

Migrations are located in `core-backend/src/main/resources/db/migration/`

**Initial Schema** (V1\_\_initial_schema.sql) - Metadata Only:

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(60) NOT NULL,
    bio TEXT CHECK (LENGTH(bio) <= 500),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Novels table (metadata only - NO full_text)
CREATE TABLE novels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    author VARCHAR(200),
    original_language VARCHAR(10),
    era VARCHAR(100),
    genre VARCHAR(100),
    publication_year INTEGER,
    isbn VARCHAR(20),
    cover_image_url VARCHAR(500),
    description TEXT,
    is_verified BOOLEAN DEFAULT false,
    creator_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Base scenarios (with VectorDB references)
CREATE TABLE base_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    base_story VARCHAR(100) NOT NULL,
    vectordb_passage_ids TEXT[],  -- Array of VectorDB document IDs
    chapter_number INTEGER,
    character_summary TEXT,
    location_summary TEXT,
    content_summary TEXT,
    tags TEXT[],
    is_verified BOOLEAN DEFAULT false,
    creator_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Root user scenarios
CREATE TABLE root_user_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    base_scenario_id UUID REFERENCES base_scenarios(id) NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,
    scenario_type VARCHAR(50) NOT NULL CHECK (scenario_type IN (
        'CHARACTER_CHANGE', 'EVENT_ALTERATION', 'SETTING_MODIFICATION'
    )),
    quality_score DECIMAL(3,2) DEFAULT 0.0,
    is_private BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leaf user scenarios (forked)
CREATE TABLE leaf_user_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_scenario_id UUID REFERENCES root_user_scenarios(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) NOT NULL,
    scenario_type VARCHAR(50) NOT NULL,
    is_private BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scenario character changes (references VectorDB)
CREATE TABLE scenario_character_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    root_scenario_id UUID REFERENCES root_user_scenarios(id) ON DELETE CASCADE,
    leaf_scenario_id UUID REFERENCES leaf_user_scenarios(id) ON DELETE CASCADE,
    character_vectordb_id VARCHAR(100) NOT NULL,  -- VectorDB character document ID
    attribute VARCHAR(100) NOT NULL,
    original_value TEXT,
    new_value TEXT NOT NULL,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (root_scenario_id IS NOT NULL AND leaf_scenario_id IS NULL) OR
        (root_scenario_id IS NULL AND leaf_scenario_id IS NOT NULL)
    )
);

-- Conversations table (with VectorDB character reference)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scenario_id UUID NOT NULL,
    scenario_type VARCHAR(20) NOT NULL CHECK (scenario_type IN ('root_user', 'leaf_user')),
    character_vectordb_id VARCHAR(100) NOT NULL,  -- VectorDB character ID
    parent_conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    is_root BOOLEAN DEFAULT true,
    message_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    is_private BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (is_root = true AND parent_conversation_id IS NULL) OR
        (is_root = false AND parent_conversation_id IS NOT NULL)
    )
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_id UUID REFERENCES users(id),
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    emotion VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation-Message join table (for message reuse)
CREATE TABLE conversation_message_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    sequence_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(conversation_id, sequence_order),
    UNIQUE(conversation_id, message_id)
);

-- Social tables
CREATE TABLE user_follows (
    follower_id UUID REFERENCES users(id) ON DELETE CASCADE,
    followee_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, followee_id),
    CHECK (follower_id != followee_id)
);

CREATE TABLE conversation_likes (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, conversation_id)
);

CREATE TABLE conversation_memos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL CHECK (LENGTH(content) <= 1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Apply Migrations

```bash
cd core-backend
./gradlew flywayMigrate

# Check migration status
./gradlew flywayInfo
```

---

## VectorDB Setup

**Story Reference**: Epic 0, Story 0.7/0.8 - Novel Ingestion Pipeline

### 1. Start ChromaDB via Docker

```bash
# Pull ChromaDB image
docker pull chromadb/chroma:latest

# Run ChromaDB container
docker run -d \
  --name chromadb \
  -p 8001:8000 \
  -v ./chroma_data:/chroma/chroma \
  chromadb/chroma:latest

# Verify ChromaDB is running
curl http://localhost:8001/api/v1/heartbeat
# Expected: {"nanosecond heartbeat": ...}
```

### 2. Initialize VectorDB Collections (Python)

Create `ai-backend/scripts/init_vectordb.py`:

```python
import chromadb
from chromadb.config import Settings

# Connect to ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_data",
    settings=Settings(anonymized_telemetry=False)
)

# Create 5 collections
collections = [
    "novel_passages",
    "characters",
    "locations",
    "events",
    "themes"
]

for collection_name in collections:
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # Cosine similarity for embeddings
    )
    print(f"✓ Created collection: {collection_name}")

print("\n✓ VectorDB initialization complete")
print(f"  - Total collections: {len(collections)}")
print(f"  - Storage path: ./chroma_data")
```

Run initialization:

```bash
cd ai-backend
python scripts/init_vectordb.py
```

### 3. Test VectorDB Connection

```python
# ai-backend/tests/test_vectordb.py
import chromadb

def test_vectordb_connection():
    client = chromadb.PersistentClient(path="./chroma_data")

    # List collections
    collections = client.list_collections()
    assert len(collections) == 5

    # Test adding a document
    passages = client.get_collection("novel_passages")
    passages.add(
        ids=["test_passage_1"],
        documents=["This is a test passage"],
        metadatas=[{"novel_id": "test", "chapter_number": 1}]
    )

    # Query test
    results = passages.get(ids=["test_passage_1"])
    assert len(results['ids']) == 1

    print("✓ VectorDB connection test passed")

if __name__ == "__main__":
    test_vectordb_connection()
```

### 4. Configure Gemini API

Create `ai-backend/.env`:

```properties
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# VectorDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_PERSIST_DIRECTORY=./chroma_data

# Embedding Configuration
EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_DIMENSION=768

# LLM Configuration
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=8192
```

Get Gemini API Key:

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env` file

### 5. Verify Gemini Integration

```python
# ai-backend/tests/test_gemini.py
import google.generativeai as genai
import os

def test_gemini_connection():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    # Test text generation
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content("Hello, World!")
    assert response.text
    print(f"✓ Text generation works: {response.text[:50]}...")

    # Test embedding generation
    result = genai.embed_content(
        model="models/text-embedding-004",
        content="Test embedding",
        task_type="retrieval_document"
    )
    assert len(result['embedding']) == 768
    print(f"✓ Embedding generation works: {len(result['embedding'])} dimensions")

if __name__ == "__main__":
    test_gemini_connection()
```

---

    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    memo_text VARCHAR(1000) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, conversation_id)

);

-- Indexes
CREATE INDEX idx_scenarios_base_story ON scenarios(base_story);
CREATE INDEX idx_scenarios_creator ON scenarios(creator_id);
CREATE INDEX idx_scenarios_quality ON scenarios(quality_score);
CREATE INDEX idx_scenarios_parameters ON scenarios USING GIN (parameters);
CREATE INDEX idx_scenarios_parent ON scenarios(parent_scenario_id);

CREATE INDEX idx_conversations_scenario ON conversations(scenario_id);
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_parent ON conversations(parent_conversation_id);

CREATE INDEX idx_messages_role ON messages(role);

CREATE INDEX idx_follows_follower ON user_follows(follower_id);
CREATE INDEX idx_follows_following ON user_follows(following_id);

CREATE INDEX idx_likes_user ON conversation_likes(user_id);
CREATE INDEX idx_likes_conversation ON conversation_likes(conversation_id);

````

**Run Migrations**:

```bash
# Migrations run automatically on Spring Boot startup
# Or run manually with Gradle
./gradlew flywayMigrate

# Check migration status
./gradlew flywayInfo
````

### 3. Seed Test Data (Optional)

```bash
# Run seed script
psql -U gaji_user -d gaji -f backend/src/main/resources/db/seed/test_data.sql
```

---

## Frontend Setup

**Story Reference**: Epic 0, Story 0.4 - Vue.js Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd gaji-workspace/frontend
```

### 2. Install Dependencies

```bash
# Using pnpm (recommended)
pnpm install

# Or using npm
npm install
```

**Key Dependencies**:

- `vue@3.3.8`
- `typescript@5.2.2`
- `vite@5.0.0`
- `@pandacss/dev@0.18.0`
- `primevue@3.46.0`
- `pinia@2.1.7`
- `vue-router@4.2.5`

### 3. Configure Environment

Create `frontend/.env.local`:

```properties
# API Configuration
VITE_API_BASE_URL=http://localhost:8080/api
VITE_AI_API_BASE_URL=http://localhost:8000

# Feature Flags
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG=true

# OAuth (if using)
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

### 4. Run Development Server

```bash
# Start Vite dev server
pnpm dev

# Or with npm
npm run dev
```

### 5. Build for Production

```bash
# Build optimized bundle
pnpm build

# Preview production build
pnpm preview
```

### 6. Verify Frontend

```bash
# Health check endpoint
curl http://localhost:5173/health

# Open in browser
open http://localhost:5173
```

**Default Port**: 5173

---

## Docker Setup

**Story Reference**: Epic 0, Story 0.5 - Docker Compose Configuration

### 1. Docker Compose File

`docker-compose.yml` (project root):

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:15-alpine
    container_name: gaji-postgres
    environment:
      POSTGRES_DB: gaji
      POSTGRES_USER: gaji_user
      POSTGRES_PASSWORD: your_password_here
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gaji_user -d gaji"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: gaji-backend
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/gaji
      SPRING_DATASOURCE_USERNAME: gaji_user
      SPRING_DATASOURCE_PASSWORD: your_password_here
      AI_BACKEND_URL: http://ai-backend:8000
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ai-backend:
    build:
      context: ./ai-backend
      dockerfile: Dockerfile
    container_name: gaji-ai-backend
    environment:
      LLM_MODEL_PATH: /models/llm-model
      LLM_MODEL_TYPE: llama
      CORE_BACKEND_URL: http://backend:8080
    volumes:
      - ./models:/models # Mount local LLM models directory
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: gaji-frontend
    environment:
      VITE_API_BASE_URL: http://localhost:8080/api
      VITE_AI_API_BASE_URL: http://localhost:8000
    ports:
      - "5173:5173"
    depends_on:
      - backend
      - ai-backend

volumes:
  postgres_data:
```

### 2. Run Full Stack

```bash
# Start all services
docker-compose up

# Run in background
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Environment Variables

### Required Variables

Create `.env` in project root:

```properties
# Database
POSTGRES_PASSWORD=your_secure_password_here

# Local LLM
LLM_MODEL_PATH=/path/to/your/llm/model
LLM_MODEL_TYPE=llama

# JWT
JWT_SECRET=your-256-bit-secret-minimum-32-characters-here

# OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Security Best Practices

- **Never commit `.env` files** to version control
- Use different secrets for dev/staging/production
- Rotate JWT secrets periodically
- Use environment-specific `.env.local`, `.env.production` files

---

## Running the Full Stack

### Option 1: Individual Services (Development)

**Terminal 1 - Database**:

```bash
docker-compose up postgres
```

**Terminal 2 - Core Backend**:

```bash
cd backend
./gradlew bootRun
```

**Terminal 3 - AI Backend**:

```bash
cd ai-backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 4 - Frontend**:

```bash
cd frontend
pnpm dev
```

### Option 2: Docker Compose (Full Stack)

```bash
# From project root
docker-compose up
```

### Option 3: Hybrid (Database + Local Services)

```bash
# Start only database
docker-compose up postgres -d

# Run backends and frontend locally (Terminals 2-4 above)
```

---

## Verification

**Story Reference**: Epic 0, Story 0.6 - Inter-Service Health Check

### Health Check Endpoints

```bash
# Core Backend
curl http://localhost:8080/actuator/health
# Expected: {"status":"UP"}

# AI Backend
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"..."}

# Frontend
curl http://localhost:5173/health
# Expected: 200 OK

# PostgreSQL
psql -U gaji_user -d gaji -c "SELECT 1;"
# Expected: 1 row returned
```

### Integration Test

```bash
# Create a test scenario (requires backend + database)
curl -X POST http://localhost:8080/api/scenarios \
  -H "Content-Type: application/json" \
  -d '{
    "base_story": "harry_potter",
    "scenario_type": "CHARACTER_CHANGE",
    "parameters": {
      "character": "Hermione Granger",
      "property": "house",
      "original_value": "Gryffindor",
      "new_value": "Slytherin"
    }
  }'

# Expected: 201 Created with scenario UUID
```

### Performance Validation

```bash
# Single scenario retrieval should be < 100ms
time curl http://localhost:8080/api/scenarios/{id}

# List scenarios should be < 200ms
time curl "http://localhost:8080/api/scenarios?page=0&size=20"
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `Port 8080 is already in use`

**Solution**:

```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or change port in application.properties
SERVER_PORT=8081
```

#### 2. Database Connection Failed

**Error**: `Connection refused: localhost:5432`

**Solutions**:

```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL
brew services start postgresql@15

# Verify credentials
psql -U gaji_user -d gaji

# Check firewall rules
sudo lsof -i :5432
```

#### 3. Flyway Migration Failed

**Error**: `Flyway migration checksum mismatch`

**Solution**:

```bash
# Repair Flyway metadata
./gradlew flywayRepair

# Or reset database (CAUTION: deletes all data)
./gradlew flywayClean flywayMigrate
```

#### 4. Frontend Build Errors

**Error**: `Module not found` or `Type error`

**Solutions**:

```bash
# Clear node_modules and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install

# Clear Vite cache
rm -rf .vite

# Check Node version
node -v  # Should be 18+
```

#### 5. AI Backend Local LLM Configuration

**Error**: `Model not found` or `Failed to load LLM`

**Solutions**:

```bash
# Verify model path
ls -lh $LLM_MODEL_PATH

# Check model compatibility
python -c "from llama_cpp import Llama; print('llama-cpp-python installed correctly')"

# Ensure sufficient GPU/CPU memory for model
# Llama-7B requires ~8GB RAM, Mistral-7B requires ~8GB RAM
# For GPU: Ensure CUDA is properly configured

# Download model if missing (example for Llama-2-7B)
# Visit https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
```

#### 6. Docker Volume Issues

**Error**: `Volume not found` or stale data

**Solutions**:

```bash
# List volumes
docker volume ls

# Remove specific volume
docker volume rm gaji_postgres_data

# Prune all unused volumes
docker volume prune

# Full reset (CAUTION)
docker-compose down -v
docker system prune -a
```

#### 7. CORS Errors

**Error**: `Access-Control-Allow-Origin` error in browser

**Solution** (backend `application.properties`):

```properties
cors.allowed.origins=http://localhost:5173,http://localhost:3000
```

#### 8. JWT Token Errors

**Error**: `Invalid JWT signature`

**Solutions**:

```bash
# Verify JWT_SECRET is set and consistent
echo $JWT_SECRET

# Check token expiration settings
JWT_ACCESS_TOKEN_EXPIRATION=3600000  # 1 hour

# Clear browser localStorage/cookies
# In browser DevTools: localStorage.clear()
```

---

## Development Workflow

### Recommended Workflow

1. **Start Database**: `docker-compose up postgres -d`
2. **Start Core Backend**: `cd gaji-workspace/core-backend && ./gradlew bootRun`
3. **Start AI Backend**: `cd gaji-workspace/ai-backend && uvicorn main:app --reload`
4. **Start Frontend**: `cd gaji-workspace/frontend && pnpm dev`
5. **Open Browser**: http://localhost:5173
6. **Check Health**: Visit health endpoints
7. **Run Tests**:
   - Backend: `cd core-backend && ./gradlew test`
   - AI Backend: `cd ai-backend && pytest`
   - Frontend: `cd frontend && pnpm test`

### Hot Reload

All services support hot reload in development:

- **Spring Boot**: Automatic with Spring DevTools
- **FastAPI**: `--reload` flag with uvicorn
- **Vue/Vite**: Built-in HMR (Hot Module Replacement)

---

## Next Steps

Once setup is complete:

1. **Read API Documentation**: `/docs/API_DOCUMENTATION.md`
2. **Review ERD**: `/docs/ERD.md`
3. **Check UI Specs**: `/docs/V0_SCREEN_SPECIFICATIONS.md`
4. **Review Story Files**: `/docs/stories/` for implementation details
5. **Run Integration Tests**: Epic 0, Story 0.6 test suite

---

## Support

- **Architecture**: See `/docs/architecture.md`
- **PRD**: See `/docs/PRD.md`
- **Story Files**: See `/docs/stories/epic-{N}-story-{M}.md`
- **Issues**: GitHub Issues
- **Questions**: Team Slack #gaji-dev
