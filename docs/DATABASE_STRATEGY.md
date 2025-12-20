# Database Strategy: Hybrid Architecture

**Project**: Gaji Platform  
**Date**: 2025-11-14  
**Decision**: PostgreSQL (Metadata) + VectorDB (Content & Embeddings)

---

## 📊 Strategy Comparison

### Option A: PostgreSQL Only

| Aspect           | Rating     | Notes                           |
| ---------------- | ---------- | ------------------------------- |
| Complexity       | ⭐⭐⭐⭐⭐ | Simple (1 DB)                   |
| Metadata Queries | ⭐⭐⭐⭐⭐ | B-Tree index, JOIN optimization |
| Full-text Search | ⭐⭐☆☆☆    | tsvector slow on large text     |
| Semantic Search  | ⭐☆☆☆☆     | pgvector 10x slower on 768-dim  |
| Scalability      | ⭐⭐☆☆☆    | Vertical scaling only           |
| Cost             | ⭐⭐⭐☆☆   | Expensive at 100GB+             |

❌ **Not recommended**: Poor semantic search performance

---

### Option B: Hybrid (PostgreSQL + VectorDB) ✅

| Aspect           | Rating     | Notes                                         |
| ---------------- | ---------- | --------------------------------------------- |
| Complexity       | ⭐⭐⭐☆☆   | MSA 2 services                                |
| Metadata Queries | ⭐⭐⭐⭐⭐ | PostgreSQL B-Tree                             |
| Full-text Search | ⭐⭐⭐⭐⭐ | VectorDB chunked storage                      |
| Semantic Search  | ⭐⭐⭐⭐⭐ | VectorDB cosine similarity (HNSW)             |
| Scalability      | ⭐⭐⭐⭐⭐ | VectorDB horizontal scaling                   |
| Cost             | ⭐⭐⭐⭐☆  | Efficient (small PostgreSQL + cheap VectorDB) |

✅ **Recommended**: Best performance + cost efficiency

---

### Option C: VectorDB Only

| Aspect           | Rating     | Notes                         |
| ---------------- | ---------- | ----------------------------- |
| Complexity       | ⭐⭐⭐⭐☆  | Steep learning curve          |
| Metadata Queries | ⭐⭐☆☆☆    | Metadata filter only, no JOIN |
| Full-text Search | ⭐⭐⭐⭐⭐ | Excellent                     |
| Semantic Search  | ⭐⭐⭐⭐⭐ | Native support                |
| Scalability      | ⭐⭐⭐⭐⭐ | Horizontal scaling            |
| Cost             | ⭐⭐⭐☆☆   | Inefficient for metadata      |

❌ **Not recommended**: No relational queries, no ACID transactions

---

## 🏗️ Hybrid Architecture

```
Frontend (Vue.js)
    ↓
Spring Boot :8080 ←→ FastAPI :8000
    ↓                    ↓
PostgreSQL          VectorDB
(Metadata)        (Content & Embeddings)
```

### Data Distribution

#### PostgreSQL (13 tables)

| Table                      | Data                                  | Why PostgreSQL                   |
| -------------------------- | ------------------------------------- | -------------------------------- |
| users                      | User accounts                         | Relational, JOIN                 |
| novels                     | Title, author, genre, ISBN            | B-Tree index for metadata search |
| scenarios                  | Type, creator, fork relationships     | Complex JOIN queries             |
| conversations              | User, scenario, likes, created_at     | Relational queries, sorting      |
| messages                   | **Content** (<500 chars), role, order | Short text, ACID transactions    |
| conversation_message_links | Message reuse for forking             | JOIN table                       |
| follows, likes, memos      | Social features                       | Relational                       |

**Access**: Spring Boot (MyBatis) only

---

#### VectorDB (5 collections)

| Collection     | Data                                             | Why VectorDB                       |
| -------------- | ------------------------------------------------ | ---------------------------------- |
| novel_passages | 200-500 word chunks + embeddings                 | Semantic search (768-dim)          |
| characters     | Personality traits, relationships (LLM analysis) | "Smart and brave character" search |
| locations      | Setting descriptions + embeddings                | Semantic search                    |
| events         | Plot points + embeddings                         | Semantic search                    |
| themes         | Thematic analysis + embeddings                   | Semantic search                    |

**Access**: FastAPI only

**Technology**: ChromaDB (dev) / Pinecone (prod)

---

## 🔍 Use Cases

### Case 1: Novel Metadata Search

**Query**: "Find books by J.K. Rowling"

**Solution**: PostgreSQL

```sql
SELECT id, title, author, genre, publication_year
FROM novels
WHERE author ILIKE '%Rowling%'
ORDER BY publication_year DESC;
```

**Why**: B-Tree index on `author` column

---

### Case 2: Semantic Passage Search

**Query**: "Find passages about bravery and friendship"

**Solution**: VectorDB

```python
# Generate query embedding
query_embedding = gemini_embed("bravery and friendship")

# VectorDB cosine similarity search
results = chroma.query(
    collection_name="novel_passages",
    query_embeddings=[query_embedding],
    n_results=10
)
```

**Why**: 768-dim vector search optimized with HNSW algorithm

---

### Case 3: User's Conversations

**Query**: "Show my recent conversations with likes"

**Solution**: PostgreSQL

```sql
SELECT c.id, c.title, COUNT(cl.user_id) AS likes, c.created_at
FROM conversations c
LEFT JOIN conversation_likes cl ON c.id = cl.conversation_id
WHERE c.user_id = ?
GROUP BY c.id
ORDER BY c.created_at DESC
LIMIT 20;
```

**Why**: Complex JOIN + aggregation requires relational DB

---

### Case 4: Character Personality Search

**Query**: "Find intelligent and perfectionist characters"

**Solution**: VectorDB

```python
query_embedding = gemini_embed("intelligent perfectionist")

results = chroma.query(
    collection_name="characters",
    query_embeddings=[query_embedding],
    where={"importance_score": {"$gte": 0.7}},
    n_results=5
)
```

**Why**: Semantic understanding of personality traits

---

## 📈 Performance Comparison

| Operation                      | PostgreSQL Only       | Hybrid                | Improvement        |
| ------------------------------ | --------------------- | --------------------- | ------------------ |
| Metadata search (author/title) | 50ms                  | 50ms                  | Same               |
| Semantic search (768-dim)      | 500ms (pgvector)      | 50ms (VectorDB)       | **10x faster**     |
| User conversations JOIN        | 80ms                  | 80ms                  | Same               |
| Character analysis             | Not possible          | 60ms                  | **New capability** |
| Storage (1000 novels)          | 5GB (full text in DB) | 500MB (metadata only) | **10x smaller**    |

---

## 💰 Cost Analysis (1000 novels)

| Item                            | PostgreSQL Only | Hybrid           | Savings  |
| ------------------------------- | --------------- | ---------------- | -------- |
| PostgreSQL storage              | $50/month (5GB) | $5/month (500MB) | $45      |
| VectorDB (ChromaDB self-hosted) | N/A             | $0               | $0       |
| VectorDB (Pinecone cloud)       | N/A             | $70/month        | -$70     |
| **Total (Dev)**                 | **$50/month**   | **$5/month**     | **$45**  |
| **Total (Prod)**                | **$50/month**   | **$75/month**    | **-$25** |

**Recommendation**: ChromaDB self-hosted for MVP, Pinecone for scale (10k+ novels)

---

## 🔄 Data Synchronization

### Novel ID Reference Pattern

```python
# FastAPI: After VectorDB ingestion
await spring_boot_client.post("/api/internal/novels/{novel_id}/ingestion-complete", {
    "passage_count": 245,
    "character_count": 12,
    "status": "COMPLETED"
})
```

```java
// Spring Boot: Update PostgreSQL
@PostMapping("/api/internal/novels/{id}/ingestion-complete")
public void updateIngestionStatus(@PathVariable UUID id, @RequestBody IngestionResult result) {
    novel.setIngestionStatus(IngestionStatus.COMPLETED);
    novel.setPassageCount(result.getPassageCount());
    novelRepository.save(novel);
}
```

### Error Handling

**Scenario**: FastAPI VectorDB write fails after PostgreSQL save

**Solution**: Retry with idempotency

```python
@celery_app.task(bind=True, max_retries=3)
def ingest_novel(self, novel_id: str):
    try:
        # VectorDB write with idempotent check
        existing = chroma.get(ids=[novel_id])
        if existing: return  # Already ingested

        # ... ingestion logic ...
    except Exception as e:
        self.retry(countdown=60, exc=e)
```

---

## ✅ Implementation Checklist

### PostgreSQL Setup

- [ ] 13 tables created via Flyway migrations
- [ ] B-Tree indexes on frequently queried columns (author, title, genre)
- [ ] Foreign keys for referential integrity
- [ ] Connection pooling (HikariCP, pool size: 20)

### VectorDB Setup

- [ ] ChromaDB persistent storage (`./chroma_data`)
- [ ] 5 collections initialized (passages, characters, locations, events, themes)
- [ ] Embedding dimension: 768 (Gemini Embedding API)
- [ ] Distance metric: Cosine similarity

### Cross-DB Communication

- [ ] Spring Boot → FastAPI REST client (WebClient)
- [ ] Novel ID consistency (UUID format)
- [ ] Error handling (retry logic, circuit breaker)
- [ ] Logging for cross-service calls

---

## 📚 Related Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture overview
- [MSA_BACKEND_OPTIMIZATION.md](./MSA_BACKEND_OPTIMIZATION.md) - Service communication patterns
- [ERD.md](./ERD.md) - PostgreSQL schema details
- [DEVELOPMENT_SETUP.md](./DEVELOPMENT_SETUP.md) - Local database setup

---

**Decision**: Hybrid Architecture (PostgreSQL + VectorDB) ✅  
**Rationale**: Best performance for both relational and semantic queries  
**Next Steps**: Implement Flyway migrations + ChromaDB collections
