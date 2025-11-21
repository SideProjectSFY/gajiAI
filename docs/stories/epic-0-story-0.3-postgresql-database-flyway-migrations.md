# Story 0.3: PostgreSQL Database Setup & Flyway Migrations (Metadata Only)

**Epic**: Epic 0 - Project Setup & Infrastructure  
**Priority**: P0 - Critical  
**Status**: Not Started  
**Estimated Effort**: 5 hours

## Description

Set up PostgreSQL database for **metadata storage only** (13 tables) using Flyway migrations. Novel content and embeddings are stored in VectorDB (ChromaDB/Pinecone). This implements the **hybrid database architecture**.

## Dependencies

**Blocks**:

- Story 1.1: Scenario Data Model (needs database)
- Story 4.1: Conversation Data Model (needs database)
- Story 6.1: User Authentication Backend (needs users table)
- All stories requiring database persistence

**Requires**:

- Story 0.1: Spring Boot Backend (Flyway integration)
- Story 0.5: Docker Configuration (PostgreSQL container)

## Acceptance Criteria

- [ ] PostgreSQL 15.x running in Docker container (port 5432)
- [ ] Database `gaji_db` created with `gaji_user` owner
- [ ] PostgreSQL extensions enabled:
  - `uuid-ossp` for UUID generation
  - `pg_trgm` for full-text search
- [ ] Flyway integrated in Spring Boot with `spring.flyway.enabled=true`
- [ ] Migration files in `/src/main/resources/db/migration/` following `V{version}__{description}.sql` naming
- [ ] **13 metadata tables total** (NO content storage):
  - **Core Tables** (3):
    - `V1__create_users_table.sql`
    - `V2__create_novels_table.sql` (metadata only, stores `vectordb_collection_id`, NO `full_text` column)
    - `V3__create_base_scenarios_table.sql` (stores VectorDB passage IDs as ARRAY)
  - **Scenario Tables** (5):
    - `V4__create_root_user_scenarios_table.sql`
    - `V5__create_leaf_user_scenarios_table.sql`
    - `V6__create_scenario_character_changes_table.sql` (stores `character_vectordb_id`)
    - `V7__create_scenario_event_alterations_table.sql` (stores `event_vectordb_id`)
    - `V8__create_scenario_setting_modifications_table.sql` (stores `location_vectordb_id`)
  - **Conversation Tables** (3):
    - `V9__create_conversations_table.sql` (stores `character_vectordb_id`)
    - `V10__create_messages_table.sql`
    - `V11__create_conversation_message_links_table.sql`
  - **Social Features** (3):
    - `V12__create_user_follows_table.sql`
    - `V13__create_conversation_likes_table.sql`
    - `V14__create_conversation_memos_table.sql`
- [ ] **Hybrid Database Cross-References**:
  - `novels.vectordb_collection_id` (VARCHAR 255) → VectorDB collection name
  - `base_scenarios.vectordb_passage_ids` (UUID[]) → VectorDB passage documents
  - `scenario_character_changes.character_vectordb_id` (UUID) → VectorDB characters collection
  - `conversations.character_vectordb_id` (UUID) → VectorDB characters collection
- [ ] **NO content columns**:
  - ❌ NO `novels.full_text` (stored in VectorDB `novel_passages` collection)
  - ❌ NO `characters` table (stored in VectorDB `characters` collection)
  - ❌ NO `locations` table (stored in VectorDB `locations` collection)
  - ❌ NO `novel_passages` table (stored in VectorDB)
  - ❌ NO JSONB columns (all data normalized in structured tables)
- [ ] CASCADE DELETE on all foreign keys for automatic cleanup
- [ ] B-tree indexes on:
  - All FK columns
  - `novels.title`, `novels.author` (search optimization)
  - `base_scenarios.novel_id`, `root_user_scenarios.base_scenario_id`
  - `conversations.user_id`, `conversations.scenario_id`
- [ ] Connection pooling configured (HikariCP):
  - Spring Boot: min 5, max 20 connections
- [ ] Database connection verified from Spring Boot
- [ ] Rollback testing: migrations can be reverted cleanly
- [ ] Development seed data migration `V15__seed_dev_data.sql` (only applied with `spring.profiles.active=dev`):
  - 10 sample users
  - 3 sample novels (metadata only, with `vectordb_collection_id`)
- [ ] Timezone set to UTC: `SET TIMEZONE='UTC';`
- [ ] Migration history tracked in `flyway_schema_history` table

## Technical Notes

**Database Design Philosophy**: **Hybrid Database Architecture** - PostgreSQL stores ONLY relational metadata (13 tables). VectorDB stores all content and embeddings (5 collections).

**Why Hybrid?**:
- **PostgreSQL**: Best for ACID transactions, complex JOINs, user data integrity
- **VectorDB**: Best for semantic search (cosine similarity), high-dimensional embeddings (768 dims)
- **Cost**: VectorDB scales better for large novel collections (~100GB vs PostgreSQL storage costs)
- **Performance**: Semantic search in VectorDB is 10x faster than pgvector for high-dimensional vectors

**Migration Sequence (14 migrations)**:

1. V1: Core users table
2. V2: Novels table (metadata only, NO full_text)
3. V3: Base scenarios (stores VectorDB references)
4. V4-5: Root/leaf user scenarios
5. V6-8: Scenario type-specific tables (character/event/setting changes)
6. V9-11: Conversation tables
7. V12-14: Social features (follows, likes, memos)
8. V15: Development seed data (dev profile only)

**VectorDB Collections** (managed by FastAPI, NOT in PostgreSQL):
- `novel_passages` (content chunks, 768-dim embeddings)
- `characters` (descriptions, personality traits)
- `locations` (settings)
- `events` (plot points)
- `themes` (thematic analysis)

**Cross-Database Data Flow Example**:
```
1. FastAPI ingests novel, stores passages in VectorDB
2. FastAPI → Spring Boot: POST /api/internal/novels (metadata only)
3. Spring Boot saves to PostgreSQL with vectordb_collection_id
4. Frontend queries Spring Boot for novel metadata
5. Spring Boot → FastAPI: Get character data from VectorDB
6. FastAPI queries VectorDB characters collection
7. FastAPI returns character data to Spring Boot
8. Spring Boot returns to frontend
```

**Example Metadata Tables (Hybrid References)**:

**V1__create_users_table.sql**:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  username VARCHAR(50) UNIQUE NOT NULL CHECK (username ~* '^[a-zA-Z0-9_]{3,50}$'),
  bio TEXT CHECK (length(bio) <= 500),
  avatar_url VARCHAR(500),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

**V2__create_novels_table.sql (Metadata Only - NO full_text)**:
```sql
CREATE TABLE novels (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(500) NOT NULL,
  author VARCHAR(200) NOT NULL,
  publication_year INTEGER,
  genre VARCHAR(100),
  vectordb_collection_id VARCHAR(255) NOT NULL UNIQUE,  -- Reference to VectorDB
  ingestion_status VARCHAR(50) DEFAULT 'pending',       -- pending, processing, completed, failed
  total_passages_count INTEGER,
  total_characters_count INTEGER,
  gutenberg_file_path VARCHAR(500),                     -- For debugging
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_novels_title ON novels(title);
CREATE INDEX idx_novels_author ON novels(author);
CREATE INDEX idx_novels_vectordb ON novels(vectordb_collection_id);
-- NOTE: NO full_text column - content is in VectorDB novel_passages collection
```

**V3__create_base_scenarios_table.sql**:
```sql
CREATE TABLE base_scenarios (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  vectordb_passage_ids UUID[] NOT NULL,  -- Array of VectorDB passage IDs
  character_vectordb_ids UUID[],         -- Array of VectorDB character IDs
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_base_scenarios_novel ON base_scenarios(novel_id);
```

**V6__create_scenario_character_changes_table.sql**:
```sql
CREATE TABLE scenario_character_changes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  scenario_id UUID NOT NULL REFERENCES root_user_scenarios(id) ON DELETE CASCADE,
  character_vectordb_id UUID NOT NULL,   -- Reference to VectorDB characters collection
  attribute VARCHAR(100) NOT NULL,       -- e.g., "house", "personality", "backstory"
  original_value TEXT,
  new_value TEXT NOT NULL,
  reasoning TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scenario_char_changes_scenario ON scenario_character_changes(scenario_id);
-- NOTE: Character data (name, description, personality) is in VectorDB
```

**V9__create_conversations_table.sql**:
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  scenario_id UUID REFERENCES root_user_scenarios(id) ON DELETE SET NULL,
  character_vectordb_id UUID NOT NULL,   -- Reference to VectorDB characters collection
  parent_conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
  title VARCHAR(200),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK (parent_conversation_id IS NULL OR 
         (SELECT parent_conversation_id FROM conversations WHERE id = parent_conversation_id) IS NULL)
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_scenario ON conversations(scenario_id);
CREATE INDEX idx_conversations_parent ON conversations(parent_conversation_id);
-- NOTE: ROOT-only forking (max depth 1)
```

**V12__create_user_follows_table.sql**:
```sql
CREATE TABLE user_follows (
  follower_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  followee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (follower_id, followee_id),
  CHECK (follower_id != followee_id)
);

CREATE INDEX idx_follows_follower ON user_follows(follower_id);
CREATE INDEX idx_follows_followee ON user_follows(followee_id);
```

**V13__create_conversation_likes_table.sql**:
```sql
CREATE TABLE conversation_likes (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, conversation_id)
);

CREATE INDEX idx_likes_user ON conversation_likes(user_id);
CREATE INDEX idx_likes_conversation ON conversation_likes(conversation_id);
```

**V14__create_conversation_memos_table.sql**:
```sql
CREATE TABLE conversation_memos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  content TEXT NOT NULL CHECK (length(content) <= 2000),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, conversation_id)
);

CREATE INDEX idx_memos_user ON conversation_memos(user_id);
CREATE INDEX idx_memos_conversation ON conversation_memos(conversation_id);
```

**V15__seed_dev_data.sql (Development Only)**:
```sql
-- Only executed when spring.profiles.active=dev
INSERT INTO users (email, password_hash, username, bio) VALUES
  ('dev@example.com', '$2a$12$hashed_password', 'dev_user', 'Development test user'),
  ('admin@example.com', '$2a$12$hashed_password', 'admin_user', 'Admin test user');

-- Insert sample novels (metadata only)
INSERT INTO novels (title, author, publication_year, genre, vectordb_collection_id, ingestion_status, total_passages_count) VALUES
  ('Pride and Prejudice', 'Jane Austen', 1813, 'Romance', 'novel_pride_and_prejudice_uuid', 'completed', 523),
  ('Great Expectations', 'Charles Dickens', 1861, 'Drama', 'novel_great_expectations_uuid', 'completed', 687),
  ('The Adventures of Tom Sawyer', 'Mark Twain', 1876, 'Adventure', 'novel_tom_sawyer_uuid', 'completed', 412);

-- NOTE: Novel content and characters are in VectorDB, NOT PostgreSQL
```
  copyright_note TEXT,        -- Detailed copyright info (e.g., 'Public domain in the USA')
  cover_image_url VARCHAR(500),
  description TEXT,
  is_verified BOOLEAN DEFAULT FALSE,
  creator_id UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_novels_series ON novels(series_title, series_number);
CREATE INDEX idx_novels_copyright ON novels(copyright_status);
```

**Example Normalized Character Tables (V7-9)**:

```sql
-- V7__create_character_aliases_table.sql
CREATE TABLE character_aliases (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  alias VARCHAR(255) NOT NULL,
  usage_context TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(character_id, alias)
);

-- V8__create_character_personality_traits_table.sql
CREATE TABLE character_personality_traits (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  trait VARCHAR(100) NOT NULL,
  intensity DECIMAL(3,2) CHECK (intensity BETWEEN 0 AND 1),
  evidence_passage_id UUID REFERENCES novel_passages(id) ON DELETE SET NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(character_id, trait)
);

-- V9__create_character_relationships_table.sql
CREATE TABLE character_relationships (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  related_character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  relationship_type VARCHAR(50) NOT NULL,
  relationship_description TEXT,
  strength DECIMAL(3,2) CHECK (strength BETWEEN 0 AND 1),
  is_mutual BOOLEAN DEFAULT FALSE,
  first_interaction_chapter_id UUID REFERENCES novel_chapters(id) ON DELETE SET NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK(character_id != related_character_id)
);
```

**Example Scenario Type-Specific Tables (V22-24)**:

```sql
-- V22__create_scenario_character_changes_table.sql
CREATE TABLE scenario_character_changes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  root_scenario_id UUID REFERENCES root_user_scenarios(id) ON DELETE CASCADE,
  leaf_scenario_id UUID REFERENCES leaf_user_scenarios(id) ON DELETE CASCADE,
  character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
  attribute VARCHAR(100) NOT NULL,
  original_value TEXT,
  new_value TEXT NOT NULL,
  reasoning TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK((root_scenario_id IS NOT NULL AND leaf_scenario_id IS NULL) OR
        (root_scenario_id IS NULL AND leaf_scenario_id IS NOT NULL))
);
```

**Seed Data (V33\_\_seed_dev_data.sql)**:

```sql
-- Only executed when spring.profiles.active=dev
INSERT INTO users (email, password_hash, username, bio) VALUES
  ('dev@example.com', '$2a$12$hashed_password', 'dev_user', 'Development test user');

-- Insert sample novel, characters, scenarios for testing
```

## QA Checklist

### Functional Testing

- [ ] PostgreSQL container starts successfully
- [ ] Database `gaji_db` accessible with credentials
- [ ] Flyway migrations execute on Spring Boot startup
- [ ] V1-V14 migrations create all 13 metadata tables
- [ ] V15__seed_dev_data.sql runs only with dev profile
- [ ] flyway_schema_history tracks migration versions

### Schema Validation

- [ ] All 13 metadata tables created successfully
- [ ] All tables have primary keys (UUID type)
- [ ] Foreign key constraints enforced with CASCADE DELETE
- [ ] UNIQUE constraints on users.email, users.username, novels.vectordb_collection_id
- [ ] CHECK constraints validate data:
  - users.username regex pattern
  - conversation_memos.content length <= 2000
  - Conversations.parent_conversation_id ROOT-only check
- [ ] B-tree indexes created on:
  - All FK columns
  - Search columns (novels.title, novels.author, users.email, users.username)
  - VectorDB reference columns (novels.vectordb_collection_id)
- [ ] UUID, pg_trgm extensions enabled (test with `SELECT uuid_generate_v4()`)
- [ ] **NO pgvector extension** (not needed - embeddings in VectorDB)
- [ ] **NO JSONB columns** exist (verify with: `SELECT table_name, column_name FROM information_schema.columns WHERE data_type = 'jsonb'` returns empty)
- [ ] **NO content tables** (verify no `novel_passages`, `characters`, `locations` tables in PostgreSQL)

### Hybrid Database Validation

- [ ] Novels table has `vectordb_collection_id` column (NOT `full_text`)
- [ ] Base scenarios table has `vectordb_passage_ids` array column
- [ ] Scenario character changes table has `character_vectordb_id` column
- [ ] Conversations table has `character_vectordb_id` column
- [ ] Seed data novels have valid `vectordb_collection_id` values
- [ ] No foreign keys to non-existent tables (e.g., NO FK to `characters` table)

### Migration Management

- [ ] Flyway baseline version set correctly
- [ ] Out-of-order migrations rejected
- [ ] Checksum validation prevents manual schema changes
- [ ] Failed migration rolls back transaction

### Performance

- [ ] Connection pool max 20 connections configured
- [ ] Connection acquisition < 50ms
- [ ] B-tree index queries on FK columns optimized (use EXPLAIN ANALYZE)
- [ ] Query performance for JOINs acceptable (<100ms for typical queries)

### Security

- [ ] Database user `gaji_user` has limited privileges (no DROP DATABASE)
- [ ] Password not hardcoded in application.yml
- [ ] SSL connection enabled for production profile

## Estimated Effort

5 hours
