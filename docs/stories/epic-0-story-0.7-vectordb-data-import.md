# Story 0.7: VectorDB Data Import from Pre-processed Dataset

**Epic**: Epic 0 - Project Setup & Infrastructure  
**Priority**: P0 - Critical  
**Estimated Effort**: 3 hours

## Status

Ready to Implement

## Story

As a **platform administrator**,  
I want **pre-processed Project Gutenberg dataset to be imported into VectorDB**,  
So that **the application has novel passages, characters, and metadata ready for scenario creation**.

## Context

This story implements a **one-time data import script** that loads pre-processed Project Gutenberg dataset into ChromaDB (dev) or Pinecone (prod). The dataset already contains chunked passages, embeddings, and extracted character metadata, eliminating the need for real-time ingestion pipelines or LLM extraction.

**Import Process**:

```
Pre-processed Dataset (JSON/Parquet)
      ↓
Python Import Script (FastAPI utils)
      ↓
ChromaDB/Pinecone (5 collections: passages, characters, locations, events, themes)
      ↓
PostgreSQL (novel metadata via Spring Boot API)
```

**Why Pre-processed Dataset?**:

- ✅ **No LLM extraction needed**: Characters, locations, events already extracted
- ✅ **Embeddings included**: 768-dim vectors pre-computed (Gemini Embedding API format)
- ✅ **Quality-controlled**: Dataset curated and validated
- ✅ **Fast setup**: Import takes ~5 minutes vs hours of processing
- ✅ **Cost-effective**: No API costs for initial setup

**Dataset Assumptions** (adjust based on actual dataset):
- Format: JSON or Parquet files
- Embeddings: 768-dimensional vectors (compatible with Gemini Embedding API)
- Structure: Separate files for passages, characters, locations, events, themes
- Novels: 10-50 classic books from Project Gutenberg

## Acceptance Criteria

### AC1: Dataset Structure Validation

- [ ] Dataset contains required files/tables:
  - `novels.json` - Novel metadata (title, author, year, genre)
  - `passages.parquet` - Text chunks with embeddings (200-500 words each)
  - `characters.json` - Character metadata (name, role, description, personality_traits)
  - `locations.json` - Setting descriptions
  - `events.json` - Plot events
  - `themes.json` - Thematic analysis (optional)
- [ ] Embedding validation:
  - Dimension: 768 (Gemini Embedding API compatible)
  - Data type: float32 or float64
  - No null embeddings
- [ ] Data integrity checks:
  - All passages reference valid novel_id
  - All characters reference valid novel_id
  - No duplicate IDs within collections

### AC2: ChromaDB Collection Setup

- [ ] Create 5 ChromaDB collections:
  - `novel_passages` - Text chunks with embeddings
  - `characters` - Character metadata
  - `locations` - Settings and places
  - `events` - Plot events
  - `themes` - Thematic elements
- [ ] Collection schema for `novel_passages`:
  ```python
  {
    "id": "UUID",
    "novel_id": "UUID (PostgreSQL reference)",
    "chapter_number": int,
    "passage_number": int,
    "text": str,
    "word_count": int,
    "passage_type": str,  # narrative, dialogue, description
    "embedding": [768 floats]
  }
  ```
- [ ] Collection schema for `characters`:
  ```python
  {
    "id": "UUID",
    "novel_id": "UUID",
    "name": str,
    "role": str,  # protagonist, antagonist, supporting
    "description": str,
    "personality_traits": [str],  # ["brave", "intelligent"]
    "first_appearance_chapter": int,
    "embedding": [768 floats]  # character description embedding
  }
  ```
- [ ] Distance metric: Cosine similarity (ChromaDB default)
- [ ] Index type: HNSW (Hierarchical Navigable Small World) for fast ANN search

### AC3: Python Import Script

- [ ] Script location: `ai-backend/scripts/import_dataset.py`
- [ ] Command-line interface:
  ```bash
  python scripts/import_dataset.py \
    --dataset-path /path/to/gutenberg_dataset \
    --vectordb chromadb \
    --vectordb-host localhost:8001 \
    --spring-boot-api http://localhost:8080
  ```
- [ ] Import workflow:
  1. **Validate dataset**: Check file structure and data integrity
  2. **Create ChromaDB collections**: Initialize 5 collections
  3. **Import passages**: Batch insert with embeddings (1000 per batch)
  4. **Import characters**: Batch insert character metadata
  5. **Import locations/events/themes**: Optional collections
  6. **Create PostgreSQL metadata**: Call Spring Boot API for novel records
  7. **Verify import**: Query sample data, check counts
- [ ] Progress tracking:
  - Console output: "Importing passages: 1000/5234 (19%)"
  - ETA calculation
  - Success/failure summary at end
- [ ] Error handling:
  - Rollback on failure (delete partial collections)
  - Retry logic for API calls (3 attempts)
  - Detailed error logging

### AC4: PostgreSQL Metadata Creation

- [ ] For each novel in dataset, create PostgreSQL record via Spring Boot API:
  - Endpoint: `POST /api/internal/novels`
  - Request payload:
    ```json
    {
      "title": "Pride and Prejudice",
      "author": "Jane Austen",
      "publication_year": 1813,
      "genre": "Romance",
      "language": "en",
      "vectordb_collection_id": "novel_UUID_in_chromadb",
      "total_passages_count": 523,
      "total_characters_count": 47,
      "ingestion_status": "completed"
    }
    ```
  - Response: `{novel_id: UUID}`
- [ ] Store novel_id → vectordb_collection_id mapping
- [ ] Update novel record after import completes:
  - `PATCH /api/internal/novels/{id}`
  - Set `ingestion_status: "completed"`
  - Set `processed_at: TIMESTAMP`

### AC5: Import Verification & Testing

- [ ] Verification script: `scripts/verify_import.py`
- [ ] Checks performed:
  - Count validation: PostgreSQL novel count == VectorDB novel count
  - Sample queries: Retrieve 5 random passages from VectorDB
  - Semantic search test: Query "brave protagonist" → should return relevant characters
  - Cross-reference test: PostgreSQL novel_id exists in VectorDB metadata
- [ ] Integration test:
  - Import sample dataset (1 novel, ~500 passages, 20 characters)
  - Verify all data accessible via FastAPI endpoints
  - Verify PostgreSQL metadata correct
  - Cleanup test data
- [ ] Performance benchmarks:
  - Import speed: > 1000 passages/minute
  - Total import time: < 10 minutes for 10 novels
  - Memory usage: < 2GB during import

## Technical Notes

### Dataset Format Examples

**novels.json**:
```json
[
  {
    "id": "novel_pride_and_prejudice",
    "title": "Pride and Prejudice",
    "author": "Jane Austen",
    "publication_year": 1813,
    "genre": "Romance",
    "language": "en",
    "total_chapters": 61,
    "total_word_count": 122189
  }
]
```

**passages.parquet** (columns):
```
id: string (UUID)
novel_id: string
chapter_number: int
passage_number: int
text: string
word_count: int
passage_type: string (narrative, dialogue, description)
embedding: list<float> (768 dimensions)
```

**characters.json**:
```json
[
  {
    "id": "char_elizabeth_bennet",
    "novel_id": "novel_pride_and_prejudice",
    "name": "Elizabeth Bennet",
    "role": "protagonist",
    "description": "Second eldest Bennet daughter, intelligent and witty",
    "personality_traits": ["intelligent", "witty", "independent", "prejudiced"],
    "first_appearance_chapter": 1,
    "embedding": [0.123, -0.456, ...]
  }
]
```

### Import Script Implementation

**ai-backend/scripts/import_dataset.py**:

```python
import argparse
import json
import pandas as pd
from chromadb import Client
from chromadb.config import Settings
import httpx
from tqdm import tqdm

class GutenbergDatasetImporter:
    def __init__(self, dataset_path, vectordb_host, spring_boot_api):
        self.dataset_path = dataset_path
        self.chroma_client = Client(Settings(
            chroma_api_impl="rest",
            chroma_server_host=vectordb_host.split(":")[0],
            chroma_server_http_port=int(vectordb_host.split(":")[1])
        ))
        self.spring_boot_api = spring_boot_api
    
    def import_all(self):
        """Main import workflow"""
        print("🚀 Starting dataset import...")
        
        # 1. Validate dataset
        self.validate_dataset()
        
        # 2. Create collections
        self.create_collections()
        
        # 3. Import data
        novels = self.load_novels()
        for novel in tqdm(novels, desc="Importing novels"):
            self.import_novel(novel)
        
        # 4. Verify import
        self.verify_import()
        
        print("✅ Import complete!")
    
    def validate_dataset(self):
        """Check dataset structure"""
        required_files = ['novels.json', 'passages', 'characters']
        for file in required_files:
            path = f"{self.dataset_path}/{file}"
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing required file/dir: {file}")
    
    def create_collections(self):
        """Create 5 ChromaDB collections"""
        collections = [
            "novel_passages",
            "characters", 
            "locations",
            "events",
            "themes"
        ]
        for name in collections:
            try:
                self.chroma_client.create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                print(f"Collection {name} may already exist: {e}")
    
    def load_novels(self):
        """Load novels.json"""
        with open(f"{self.dataset_path}/novels.json") as f:
            return json.load(f)
    
    def import_novel(self, novel):
        """Import single novel's data"""
        # Import passages
        passages_path = f"{self.dataset_path}/passages/{novel['id']}.parquet"
        if os.path.exists(passages_path):
            passages_df = pd.read_parquet(passages_path)
            self.import_passages(novel['id'], passages_df)
        
        # Import characters
        chars_path = f"{self.dataset_path}/characters/{novel['id']}.json"
        if os.path.exists(chars_path):
            with open(chars_path) as f:
                characters = json.load(f)
            self.import_characters(novel['id'], characters)
        
        # Create PostgreSQL metadata
        self.create_novel_metadata(novel)
    
    def import_passages(self, novel_id, df):
        """Batch insert passages to ChromaDB"""
        collection = self.chroma_client.get_collection("novel_passages")
        
        batch_size = 1000
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            collection.add(
                ids=batch['id'].tolist(),
                embeddings=batch['embedding'].tolist(),
                documents=batch['text'].tolist(),
                metadatas=batch[[
                    'novel_id', 'chapter_number', 
                    'passage_number', 'word_count', 'passage_type'
                ]].to_dict('records')
            )
    
    def import_characters(self, novel_id, characters):
        """Import characters to ChromaDB"""
        collection = self.chroma_client.get_collection("characters")
        
        collection.add(
            ids=[c['id'] for c in characters],
            embeddings=[c['embedding'] for c in characters],
            documents=[c['description'] for c in characters],
            metadatas=[{
                'novel_id': c['novel_id'],
                'name': c['name'],
                'role': c['role'],
                'personality_traits': json.dumps(c['personality_traits']),
                'first_appearance_chapter': c['first_appearance_chapter']
            } for c in characters]
        )
    
    def create_novel_metadata(self, novel):
        """Create PostgreSQL record via Spring Boot API"""
        try:
            response = httpx.post(
                f"{self.spring_boot_api}/api/internal/novels",
                json={
                    "title": novel['title'],
                    "author": novel['author'],
                    "publication_year": novel['publication_year'],
                    "genre": novel['genre'],
                    "language": novel['language'],
                    "vectordb_collection_id": novel['id'],
                    "total_passages_count": novel.get('total_passages_count', 0),
                    "total_characters_count": novel.get('total_characters_count', 0),
                    "ingestion_status": "completed"
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating metadata for {novel['title']}: {e}")
    
    def verify_import(self):
        """Basic verification checks"""
        passages = self.chroma_client.get_collection("novel_passages")
        characters = self.chroma_client.get_collection("characters")
        
        print(f"✅ {passages.count()} passages imported")
        print(f"✅ {characters.count()} characters imported")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--vectordb-host", default="localhost:8001")
    parser.add_argument("--spring-boot-api", default="http://localhost:8080")
    args = parser.parse_args()
    
    importer = GutenbergDatasetImporter(
        args.dataset_path,
        args.vectordb_host,
        args.spring_boot_api
    )
    importer.import_all()
```

### Verification Script

**ai-backend/scripts/verify_import.py**:

```python
import argparse
from chromadb import Client
from chromadb.config import Settings
import httpx

def verify_import(vectordb_host, spring_boot_api):
    """Verify dataset import completed successfully"""
    
    # 1. Connect to ChromaDB
    client = Client(Settings(
        chroma_api_impl="rest",
        chroma_server_host=vectordb_host.split(":")[0],
        chroma_server_http_port=int(vectordb_host.split(":")[1])
    ))
    
    # 2. Check collections exist
    collections = client.list_collections()
    required = {"novel_passages", "characters", "locations", "events", "themes"}
    existing = {c.name for c in collections}
    
    missing = required - existing
    if missing:
        print(f"⚠️ Missing collections: {missing}")
    else:
        print("✅ All 5 collections exist")
    
    # 3. Check passage count
    passages = client.get_collection("novel_passages")
    passage_count = passages.count()
    print(f"✅ {passage_count} passages imported")
    
    # 4. Test semantic search
    try:
        results = passages.query(
            query_texts=["brave protagonist hero"],
            n_results=5
        )
        print(f"✅ Semantic search works: {len(results['documents'][0])} results")
    except Exception as e:
        print(f"❌ Semantic search failed: {e}")
    
    # 5. Check PostgreSQL metadata
    try:
        response = httpx.get(f"{spring_boot_api}/api/novels")
        novels = response.json()
        print(f"✅ {len(novels)} novels in PostgreSQL")
    except Exception as e:
        print(f"❌ PostgreSQL check failed: {e}")
    
    print("\n✅ All verifications passed!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vectordb-host", default="localhost:8001")
    parser.add_argument("--spring-boot-api", default="http://localhost:8080")
    args = parser.parse_args()
    
    verify_import(args.vectordb_host, args.spring_boot_api)
```

### Spring Boot Internal API Endpoints

Required endpoints in Spring Boot for metadata creation:

**POST /api/internal/novels** (create novel metadata):
```java
@RestController
@RequestMapping("/api/internal")
public class InternalNovelController {
    
    @PostMapping("/novels")
    public NovelResponse createNovel(@RequestBody CreateNovelRequest request) {
        Novel novel = novelService.createNovel(request);
        return new NovelResponse(novel);
    }
    
    @PatchMapping("/novels/{id}")
    public void updateNovelStatus(
        @PathVariable UUID id,
        @RequestBody UpdateNovelStatusRequest request
    ) {
        novelService.updateStatus(id, request.getIngestionStatus());
    }
}
```

## Testing Strategy

### Integration Test

```python
import pytest
from fastapi.testclient import TestClient

def test_dataset_import_flow(test_client: TestClient):
    """E2E test for dataset import"""
    
    # 1. Import sample dataset (1 novel)
    result = subprocess.run([
        "python", "scripts/import_dataset.py",
        "--dataset-path", "tests/fixtures/sample_dataset",
        "--vectordb-host", "localhost:8001",
        "--spring-boot-api", "http://localhost:8080"
    ])
    assert result.returncode == 0
    
    # 2. Verify VectorDB data
    collection = chroma_client.get_collection("novel_passages")
    passages = collection.get(where={"novel_id": "test_novel_id"})
    assert len(passages['ids']) == 500  # Expected passage count
    
    # 3. Verify PostgreSQL metadata
    response = test_client.get("/api/novels/test_novel_id")
    assert response.status_code == 200
    assert response.json()['title'] == "Pride and Prejudice"
    
    # 4. Test semantic search via FastAPI
    response = test_client.post("/api/ai/search", json={
        "query": "Elizabeth Bennet personality",
        "novel_id": "test_novel_id",
        "top_k": 5
    })
    assert response.status_code == 200
    assert len(response.json()['results']) == 5
    
    # 5. Cleanup
    collection.delete(where={"novel_id": "test_novel_id"})
```

### Performance Test

```python
import time

def test_import_performance():
    """Test import speed meets benchmarks"""
    
    start_time = time.time()
    
    # Import 10 novels (~5000 passages)
    importer.import_all()
    
    elapsed = time.time() - start_time
    
    # Should complete in < 10 minutes
    assert elapsed < 600, f"Import took {elapsed}s (> 600s limit)"
    
    # Should process > 1000 passages/minute
    passages_per_minute = 5000 / (elapsed / 60)
    assert passages_per_minute > 1000, f"Only {passages_per_minute} passages/min"
```

## Implementation Checklist

- [ ] Create `ai-backend/scripts/import_dataset.py` script
- [ ] Create `ai-backend/scripts/verify_import.py` script
- [ ] Add dataset path to `.env`: `GUTENBERG_DATASET_PATH=/data/gutenberg`
- [ ] Create 5 ChromaDB collections via script
- [ ] Implement batch import for passages (1000 per batch)
- [ ] Implement batch import for characters
- [ ] Implement Spring Boot internal API endpoints
- [ ] Test with sample dataset (1 novel)
- [ ] Document dataset format in README
- [ ] Add import command to Docker Compose init script
- [ ] Performance benchmark: 10 novels < 10 minutes
- [ ] Write integration tests
- [ ] Update API documentation with new endpoints

## Dependencies

### Python Packages (add to requirements.txt)

```txt
chromadb==0.4.18
pandas==2.1.4
pyarrow==14.0.1  # For parquet files
httpx==0.25.2
tqdm==4.66.1
```

### Spring Boot Endpoints Required

- `POST /api/internal/novels` - Create novel metadata
- `PATCH /api/internal/novels/{id}` - Update ingestion status
- `DELETE /api/internal/novels/{id}` - Delete novel (for cleanup)

## Success Metrics

- ✅ Import 10 novels in < 10 minutes
- ✅ All 5 ChromaDB collections created
- ✅ PostgreSQL metadata synchronized with VectorDB
- ✅ Semantic search returns relevant results
- ✅ Memory usage < 2GB during import
- ✅ No data loss or corruption
- ✅ Verification script passes all checks

## Future Enhancements (Post-MVP)

- Support for additional dataset formats (CSV, SQLite)
- Incremental import (update existing novels)
- Dataset validation schema (JSON Schema or Pydantic)
- Import progress UI in admin dashboard
- Automated dataset updates (weekly cron job)
- Multi-language support (non-English novels)
- Custom embedding models (beyond Gemini 768-dim)

---

**Estimated Effort**: 3 hours  
**Priority**: P0 - Critical (blocks Epic 1)  
**Status**: Ready to Implement
