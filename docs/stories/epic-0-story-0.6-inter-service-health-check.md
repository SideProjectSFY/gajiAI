# Story 0.6: Inter-Service Health Check & API Contract (Pattern B)

**Epic**: Epic 0 - Project Setup & Infrastructure  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 5 hours

## Description

Implement comprehensive health check system with **Pattern B architecture** validation: Spring Boot API Gateway checks FastAPI internal service, PostgreSQL, and ChromaDB. Includes API contract verification for Spring Boot ↔ FastAPI proxy integration.

## Dependencies

**Blocks**:

- All Epic 1-6 stories (ensures stable foundation)

**Requires**:

- Story 0.5: Docker Configuration (uses Docker network for health checks)

## Acceptance Criteria

- [ ] **Spring Boot `/actuator/health`** endpoint includes custom health indicators:
  - PostgreSQL connection (metadata database)
  - FastAPI service availability (internal proxy health)
  - **Redis connection** (Long Polling + Celery broker)
  - Disk space
  - Example response:
    ```json
    {
      "status": "UP",
      "components": {
        "db": {
          "status": "UP",
          "details": {
            "database": "PostgreSQL",
            "validationQuery": "isValid()"
          }
        },
        "fastapi": {
          "status": "UP",
          "details": { "url": "http://ai-service:8000", "responseTime": "45ms" }
        },
        "redis": {
          "status": "UP",
          "details": { "host": "redis:6379", "ping": "PONG" }
        },
        "diskSpace": { "status": "UP" }
      }
    }
    ```
- [ ] **FastAPI `/health`** endpoint validates:
  - Gemini API connectivity (test API call)
  - **VectorDB connection** (ChromaDB dev / Pinecone prod)
  - Redis connection (Celery broker + Long Polling storage)
  - Celery workers active
  - Example response:
    ```json
    {
      "status": "healthy",
      "gemini_api": "connected",
      "vectordb": "connected",
      "vectordb_type": "chromadb",
      "vectordb_collections": 5,
      "redis": "connected",
      "redis_long_polling_ttl": "600s",
      "celery_workers": 2,
      "timestamp": "2025-11-14T12:00:00Z"
    }
    ```
- [ ] **Frontend `/health`** endpoint (optional):
  - Build version
  - Backend connectivity
  - Environment (dev/prod)
- [ ] **Startup validation script** `scripts/verify-stack.sh`:
  - Checks all services in sequence
  - Waits for services to be healthy (max 3 minutes timeout)
  - Validates Pattern B architecture (FastAPI not externally accessible)
- [ ] **API contract tests** verify:
  - Spring Boot → FastAPI proxy integration
  - Request/response schema compatibility
  - Error handling (4xx/5xx responses)
- [ ] **Health check dashboard** accessible at `http://localhost:8080/actuator/health`
- [ ] Failing health check returns **503 Service Unavailable** with detailed error
- [ ] **Prometheus metrics** exposed at `/actuator/prometheus` for monitoring
- [ ] **Integration tests** validate full request flow:
  - Frontend → Spring Boot → FastAPI → Gemini API
  - Frontend → Spring Boot → PostgreSQL

## Technical Notes

**Spring Boot Custom Health Indicator (FastAPI Internal Service)**:

```java
@Component
public class FastApiHealthIndicator implements HealthIndicator {

    @Value("${fastapi.base-url}")
    private String fastApiUrl;

    @Autowired
    private WebClient fastApiClient;

    @Override
    public Health health() {
        try {
            long startTime = System.currentTimeMillis();

            String response = fastApiClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(String.class)
                .block(Duration.ofSeconds(5));

            long responseTime = System.currentTimeMillis() - startTime;

            return Health.up()
                .withDetail("fastapi-service", "Available")
                .withDetail("url", fastApiUrl)
                .withDetail("responseTime", responseTime + "ms")
                .build();
        } catch (Exception e) {
            return Health.down()
                .withDetail("fastapi-service", "Unavailable")
                .withDetail("error", e.getMessage())
                .withDetail("url", fastApiUrl)
                .build();
        }
    }
}
```

**FastAPI Health Endpoint (ai-backend/app/api/health.py)**:

```python
from fastapi import APIRouter
import google.generativeai as genai
import chromadb
import redis
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    # Check Gemini API
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.5-flash')
        # Test with minimal request
        response = model.generate_content("test", generation_config={'max_output_tokens': 1})
        health_status["gemini_api"] = "connected"
    except Exception as e:
        health_status["gemini_api"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check VectorDB (ChromaDB or Pinecone)
    try:
        vectordb_type = os.getenv("VECTORDB_TYPE", "chromadb")

        if vectordb_type == "chromadb":
            client = chromadb.HttpClient(
                host=os.getenv("CHROMADB_HOST", "localhost"),
                port=int(os.getenv("CHROMADB_PORT", "8000"))
            )
            client.heartbeat()
            # Count collections
            collections = client.list_collections()
            health_status["vectordb"] = "connected"
            health_status["vectordb_type"] = "chromadb"
            health_status["vectordb_collections"] = len(collections)
        else:  # Pinecone
            # Pinecone health check logic
            health_status["vectordb"] = "connected"
            health_status["vectordb_type"] = "pinecone"
    except Exception as e:
        health_status["vectordb"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis (Celery broker + Long Polling storage)
    try:
        r = redis.Redis.from_url(os.getenv("REDIS_URL"))
        r.ping()
        health_status["redis"] = "connected"
        health_status["redis_long_polling_ttl"] = "600s"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Celery workers
    try:
        from app.celery_app import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        health_status["celery_workers"] = len(active_workers) if active_workers else 0
    except Exception as e:
        health_status["celery_workers"] = 0

    return health_status
```

**Verification Script** (`scripts/verify-stack.sh`):

```bash
#!/bin/bash

echo "🔍 Verifying Gaji Stack Health (Pattern B Architecture)..."

MAX_WAIT=180  # 3 minutes
WAIT_INTERVAL=5

wait_for_service() {
  local service_name=$1
  local health_url=$2
  local elapsed=0

  echo "⏳ Waiting for $service_name..."

  while [ $elapsed -lt $MAX_WAIT ]; do
    if curl -f -s "$health_url" > /dev/null 2>&1; then
      echo "✅ $service_name: Healthy"
      return 0
    fi
    sleep $WAIT_INTERVAL
    elapsed=$((elapsed + WAIT_INTERVAL))
    echo "   ... still waiting ($elapsed/$MAX_WAIT seconds)"
  done

  echo "❌ $service_name: Timeout after $MAX_WAIT seconds"
  return 1
}

# Check PostgreSQL
wait_for_service "PostgreSQL" "http://localhost:5432" || exit 1

# Check Redis
if redis-cli -h localhost -p 6379 ping > /dev/null 2>&1; then
  echo "✅ Redis: Healthy"
else
  echo "❌ Redis: Not responding"
  exit 1
fi

# Check ChromaDB
wait_for_service "ChromaDB" "http://localhost:8001/api/v1/heartbeat" || exit 1

# Check Spring Boot Backend (API Gateway)
wait_for_service "Backend (API Gateway)" "http://localhost:8080/actuator/health" || exit 1

# Verify FastAPI is NOT externally accessible (Pattern B security check)
if curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
  echo "⚠️  WARNING: FastAPI is externally accessible (should be internal-only)"
  echo "   Pattern B architecture violation detected!"
  exit 1
else
  echo "✅ FastAPI: Correctly configured as internal-only (Pattern B)"
fi

# Check Frontend
wait_for_service "Frontend" "http://localhost:3000" || exit 1

# Validate Pattern B architecture
echo ""
echo "🔐 Validating Pattern B Architecture..."

# Test that frontend can reach backend
if curl -f -s "http://localhost:8080/actuator/health" > /dev/null 2>&1; then
  echo "✅ Frontend → Backend: OK"
else
  echo "❌ Frontend → Backend: Failed"
  exit 1
fi

# Test that backend can reach FastAPI (via Spring Boot health check)
backend_health=$(curl -s "http://localhost:8080/actuator/health")
if echo "$backend_health" | grep -q '"fastapi":{"status":"UP"'; then
  echo "✅ Backend → FastAPI (internal): OK"
else
  echo "❌ Backend → FastAPI (internal): Failed"
  exit 1
fi

echo ""
echo "🎉 All services healthy! Pattern B architecture validated."
echo ""
echo "📊 Service URLs:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8080"
echo "   ChromaDB:  http://localhost:8001 (dev only)"
echo "   FastAPI:   Internal only (not exposed)"
```

## QA Checklist

### Functional Testing

- [ ] All health endpoints return correct status
- [ ] PostgreSQL connection failure triggers DOWN status in Spring Boot health
- [ ] FastAPI unavailable triggers DOWN status in Spring Boot health
- [ ] Gemini API connection failure detected in FastAPI health check
- [ ] ChromaDB connection failure detected in FastAPI health check
- [ ] Redis connection failure detected in FastAPI health check
- [ ] `verify-stack.sh` script detects all service states correctly
- [ ] Script waits for services to become healthy (max 3 minutes)
- [ ] Script validates Pattern B architecture (FastAPI not externally accessible)

### Health Indicator Validation

- [ ] Spring Boot `/actuator/health` includes:
  - `db` (PostgreSQL)
  - `fastapi` (internal service)
  - `diskSpace`
- [ ] FastAPI `/health` includes:
  - `gemini_api` status
  - `vectordb` status and type
  - `redis` status
  - `celery_workers` count
- [ ] Frontend `/health` includes (optional):
  - `build_version`
  - `backend_connectivity`
  - `environment` (dev/prod)
- [ ] Health details include actionable error messages
- [ ] Response times included in health check details

### API Contract Testing

- [ ] Spring Boot → FastAPI proxy contract verified:
  - `/api/v1/ai/chat/{id}/stream` proxies correctly
  - `/api/v1/ai/ingestion/novels` proxies correctly
- [ ] Frontend → Backend authentication flow contract verified
- [ ] Contract tests fail on schema mismatch
- [ ] Error responses (4xx/5xx) handled gracefully

### Pattern B Architecture Validation

- [ ] FastAPI is NOT accessible from host (port 8000 not exposed)
- [ ] Spring Boot can reach FastAPI at `http://ai-service:8000`
- [ ] Frontend can ONLY reach Spring Boot (NOT FastAPI)
- [ ] Gemini API key NOT visible in frontend network requests
- [ ] `verify-stack.sh` confirms Pattern B architecture

### Performance

- [ ] Health check responses < 200ms (all services)
- [ ] Concurrent health checks supported (10 requests/sec)
- [ ] No health check causes service slowdown
- [ ] Prometheus metrics collection overhead < 10ms

### Monitoring

- [ ] Prometheus metrics exposed at `/actuator/prometheus`
- [ ] Metrics include:
  - `http_server_requests_seconds` (request duration)
  - `jvm_memory_used_bytes` (memory usage)
  - `fastapi_health_check_duration_seconds` (FastAPI response time)
- [ ] Health status changes logged with timestamps
- [ ] Error logs include correlation IDs for debugging

### Integration Testing

- [ ] Full request flow test: Frontend → Spring Boot → FastAPI → Gemini API
- [ ] Database query flow test: Frontend → Spring Boot → PostgreSQL
- [ ] VectorDB query flow test: Frontend → Spring Boot → FastAPI → ChromaDB
- [ ] Error propagation test: Gemini API error → FastAPI → Spring Boot → Frontend

### Security

- [ ] FastAPI health endpoint accessible only from Docker network
- [ ] Gemini API key not exposed in health check responses
- [ ] Database credentials not exposed in health details
- [ ] Health check doesn't leak sensitive system information

## Estimated Effort

5 hours

## Estimated Effort

4 hours
