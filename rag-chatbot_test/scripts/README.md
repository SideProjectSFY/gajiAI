# VectorDB Import Scripts

This directory contains scripts for importing pre-processed Project Gutenberg datasets into ChromaDB/Pinecone.

## Scripts

| Script | Description |
|--------|-------------|
| `import_dataset.py` | Main import script - imports dataset to VectorDB and creates PostgreSQL metadata |
| `verify_import.py` | Verification script - validates import completeness |
| `collect_data.py` | Data collection from Project Gutenberg |
| `preprocess_text.py` | Text preprocessing and chunking |
| `generate_embeddings.py` | Embedding generation using Gemini API |
| `import_to_chromadb.py` | Legacy single-book import (use `import_dataset.py` instead) |

## Dataset Format

The import script expects a directory with the following structure:

```
dataset/
├── novels.json                    # Required: Novel metadata
├── passages/                      # Required: Text passages with embeddings
│   ├── {novel_id}.json           # or .parquet
│   └── ...
├── characters/                    # Optional: Character metadata
│   ├── {novel_id}.json
│   └── ...
├── locations/                     # Optional: Location metadata
│   ├── {novel_id}.json
│   └── ...
├── events/                        # Optional: Event metadata
│   ├── {novel_id}.json
│   └── ...
└── themes/                        # Optional: Theme metadata
    ├── {novel_id}.json
    └── ...
```

### novels.json

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

### passages/{novel_id}.json

```json
{
  "novel_id": "novel_pride_and_prejudice",
  "passages": [
    {
      "id": "pp_passage_001",
      "chapter_number": 1,
      "passage_number": 1,
      "text": "It is a truth universally acknowledged...",
      "word_count": 71,
      "passage_type": "narrative",
      "embedding": [0.1, -0.2, 0.3, ...]  // 768 dimensions
    }
  ]
}
```

### characters/{novel_id}.json

```json
[
  {
    "id": "char_elizabeth_bennet",
    "novel_id": "novel_pride_and_prejudice",
    "name": "Elizabeth Bennet",
    "role": "protagonist",
    "description": "Second eldest Bennet daughter, intelligent and witty",
    "personality_traits": ["intelligent", "witty", "independent"],
    "first_appearance_chapter": 1,
    "embedding": [0.15, -0.25, ...]  // 768 dimensions
  }
]
```

## Usage

### Prerequisites

```bash
# Install dependencies
cd gajiAI/rag-chatbot_test
pip install -r requirements.txt

# Start services (Docker)
docker-compose up -d postgres chromadb
```

### Validate Dataset

```bash
python scripts/import_dataset.py \
  --dataset-path ./data/gutenberg_dataset \
  --validate-only
```

### Dry Run (No Actual Import)

```bash
python scripts/import_dataset.py \
  --dataset-path ./data/gutenberg_dataset \
  --dry-run
```

### Full Import

```bash
# ChromaDB (Docker)
python scripts/import_dataset.py \
  --dataset-path ./data/gutenberg_dataset \
  --vectordb chromadb \
  --vectordb-host localhost:8001 \
  --spring-boot-api http://localhost:8080

# ChromaDB (Local persistent)
python scripts/import_dataset.py \
  --dataset-path ./data/gutenberg_dataset \
  --vectordb chromadb \
  --vectordb-host ./chroma_data \
  --spring-boot-api http://localhost:8080
```

### Verify Import

```bash
# Basic verification
python scripts/verify_import.py \
  --vectordb-host localhost:8001 \
  --spring-boot-api http://localhost:8080

# Generate JSON report
python scripts/verify_import.py \
  --vectordb-host localhost:8001 \
  --report \
  --output verification_report.json
```

## VectorDB Collections

The import creates 5 collections in ChromaDB:

| Collection | Description | Schema |
|------------|-------------|--------|
| `novel_passages` | Text chunks with embeddings | id, novel_id, chapter_number, passage_number, text, word_count, passage_type, embedding |
| `characters` | Character metadata | id, novel_id, name, role, description, personality_traits, first_appearance_chapter, embedding |
| `locations` | Setting descriptions | id, novel_id, name, description, embedding |
| `events` | Plot events | id, novel_id, name, description, embedding |
| `themes` | Thematic elements | id, novel_id, name, description, embedding |

## Embedding Requirements

- **Dimension**: 768 (Gemini Embedding API compatible)
- **Data type**: float32 or float64
- **Distance metric**: Cosine similarity

## Spring Boot API Integration

The import script calls Spring Boot internal API to create PostgreSQL metadata:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/internal/novels` | POST | Create novel metadata |
| `/api/internal/novels/{id}` | PATCH | Update ingestion status |
| `/api/internal/novels/{id}` | DELETE | Delete novel (cleanup) |

## Performance

- **Import speed**: > 1000 passages/minute
- **Batch size**: 1000 documents per batch
- **Retry logic**: 3 attempts with exponential backoff

## Troubleshooting

### ChromaDB Connection Error

```bash
# Check if ChromaDB is running
docker-compose ps chromadb

# Check ChromaDB logs
docker-compose logs chromadb
```

### Spring Boot Connection Error

```bash
# The import script will continue even if Spring Boot is unavailable
# PostgreSQL metadata will need to be created manually later
```

### Embedding Dimension Mismatch

```
Error: 임베딩 차원 불일치: 512 (expected: 768)
```

Ensure your embeddings are generated using Gemini Embedding API (768 dimensions).
