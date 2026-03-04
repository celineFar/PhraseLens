# Implementation Plan — Content Search v1.0

---

## 1. System Overview

Content Search is a text retrieval application that operates on a large corpus of textual data — including movie transcripts, TV series transcripts, books, and scripts. It enables users to search this corpus via three complementary retrieval strategies:

- **Exact match search** with morphological normalization (lemmatization, verb conjugations, plural forms)
- **Semantic search** using vector embeddings to find conceptually related passages
- **Multi-word expression detection** for idioms, phrasal verbs, and collocations

For each match, the system returns the matched snippet, its source metadata, location within the source, and surrounding context.

---

## 2. System Architecture

### Recommended Architecture: Modular Monolith

A modular monolith is the best fit for this project because:

- The team/scope is small — no operational overhead of microservices
- All modules share the same corpus data, so tight coupling is natural
- Modules can be extracted into separate services later if scaling demands it
- Simpler deployment and debugging during early development

### High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│                    API Layer (REST)                   │
│               (FastAPI / Express.js)                 │
├──────────────────────────────────────────────────────┤
│                   Search Orchestrator                │
│         (routes queries to the right engine)         │
├────────────┬─────────────┬───────────────────────────┤
│  Exact     │  Semantic   │  Multi-Word Expression    │
│  Match     │  Search     │  Engine (Idioms, Phrasal  │
│  Engine    │  Engine     │  Verbs, Collocations)     │
├────────────┴─────────────┴───────────────────────────┤
│              NLP Pipeline (spaCy / NLTK)             │
│     (tokenization, lemmatization, POS tagging)       │
├──────────────────────────────────────────────────────┤
│                    Data Layer                        │
│     PostgreSQL (full-text)  +  Vector DB (embeddings)│
├──────────────────────────────────────────────────────┤
│              Ingestion Pipeline                      │
│   (parse → normalize → chunk → embed → store)       │
└──────────────────────────────────────────────────────┘
```

### Technology Recommendations

| Concern              | Technology                                           |
|----------------------|------------------------------------------------------|
| Language             | Python 3.11+                                         |
| API Framework        | FastAPI                                              |
| NLP / Lemmatization  | spaCy (with `en_core_web_sm` or `_md` model)         |
| Embeddings           | Sentence-Transformers (`all-MiniLM-L6-v2` or similar)|
| Vector Store         | ChromaDB (dev/MVP) or pgvector (production)          |
| Relational DB        | PostgreSQL with `pg_trgm` + full-text search         |
| Task Queue           | Celery + Redis (for ingestion jobs)                  |
| Frontend (optional)  | React or plain HTML + HTMX for a lightweight UI      |
| Containerization     | Docker + Docker Compose                              |

---

## 3. Components

### 3.1 Ingestion Pipeline

**Responsibility:** Parse raw source files, normalize text, chunk it into searchable passages, generate embeddings, and store everything in the database.

- Accepts multiple input formats (plain text, SRT subtitles, PDF, EPUB)
- Extracts metadata (title, author/director, year, episode info)
- Splits text into passages/chunks (configurable window size, e.g., 3–5 sentences)
- Runs NLP preprocessing: tokenization, lemmatization, POS tagging
- Generates vector embeddings for each chunk
- Stores structured data in PostgreSQL and vectors in the vector store

### 3.2 NLP Pipeline

**Responsibility:** Provide shared text processing utilities used by both ingestion and search.

- Tokenization and sentence segmentation
- Lemmatization and morphological normalization
- POS tagging (needed for phrasal verb detection)
- Stop-word handling

### 3.3 Search Orchestrator

**Responsibility:** Accept user queries, determine the search mode, delegate to the appropriate engine(s), and merge/rank results.

- Parses the incoming query and its parameters (mode, filters, context window size)
- Routes to Exact Match, Semantic, or Multi-Word Expression engine
- Supports hybrid queries (combine exact + semantic results)
- Merges, deduplicates, and ranks results before returning

### 3.4 Exact Match Engine

**Responsibility:** Find literal occurrences of a query term, accounting for morphological variations.

- Lemmatizes the query term
- Queries PostgreSQL full-text search index (using `tsvector` / `tsquery`)
- Falls back to trigram similarity (`pg_trgm`) for fuzzy matching
- Returns matching passages with highlight positions

### 3.5 Semantic Search Engine

**Responsibility:** Find passages that are conceptually related to the query.

- Embeds the query using the same model used at ingestion time
- Performs nearest-neighbor search in the vector store
- Returns top-K results ranked by cosine similarity
- Applies a configurable similarity threshold to filter noise

### 3.6 Multi-Word Expression (MWE) Engine

**Responsibility:** Detect and retrieve idioms, phrasal verbs, and collocations.

- **Idiom detector:**
  - Maintains a precompiled idiom lexicon (JSON/DB table)
  - Matches query against lexicon entries
  - Handles grammatical variations via lemmatized pattern matching
  - Falls back to semantic search for idiomatic usage detection
- **Phrasal verb detector:**
  - Maintains a phrasal verb dictionary with known verb+particle pairs
  - Handles particle separation ("turn off the lights" / "turn the lights off")
  - Applies verb conjugation normalization
  - Uses POS-tag patterns to detect split constructions
- **Collocation detector:**
  - Precomputed co-occurrence statistics (PMI scores) stored in DB
  - Predefined collocation dictionary for common pairs
  - Given a target word, retrieves its top collocates from corpus statistics
  - Given a specific collocation, searches for its occurrences (exact + variant matching)

### 3.7 API Layer

**Responsibility:** Expose REST endpoints for search and corpus management.

Key endpoints:

| Method | Endpoint                     | Description                          |
|--------|------------------------------|--------------------------------------|
| POST   | `/api/search`                | Execute a search query               |
| GET    | `/api/sources`               | List all sources in the corpus       |
| GET    | `/api/sources/{id}`          | Get source metadata and stats        |
| POST   | `/api/ingest`                | Upload and ingest a new source       |
| GET    | `/api/collocations/{word}`   | Get collocates for a target word     |

### 3.8 Data Access Layer

**Responsibility:** Abstract database interactions behind a clean repository interface.

- SQLAlchemy models and repositories for relational data
- Vector store client wrapper for embedding operations
- Connection pooling and transaction management

---

## 4. Data Model

### 4.1 Key Entities

```
┌─────────────┐       ┌──────────────┐       ┌──────────────────┐
│   Source     │ 1───* │   Passage    │ 1───1 │  PassageEmbedding│
│             │       │              │       │                  │
│ id (PK)     │       │ id (PK)      │       │ passage_id (FK)  │
│ title       │       │ source_id(FK)│       │ embedding (vec)  │
│ type        │       │ text         │       └──────────────────┘
│ author      │       │ start_pos    │
│ year        │       │ end_pos      │       ┌──────────────────┐
│ metadata    │       │ chapter/ep   │       │  LemmaIndex      │
│ created_at  │       │ tokens (json)│       │                  │
└─────────────┘       │ lemmas (json)│       │ lemma            │
                      └──────────────┘       │ passage_id (FK)  │
                                             │ positions (json) │
┌─────────────────┐                          └──────────────────┘
│   Idiom         │
│                 │       ┌──────────────────┐
│ id (PK)        │       │  Collocation     │
│ canonical_form │       │                  │
│ lemma_pattern  │       │ id (PK)          │
│ definition     │       │ word1            │
└─────────────────┘       │ word2            │
                          │ pmi_score        │
                          │ frequency        │
┌─────────────────┐       └──────────────────┘
│  PhrasalVerb    │
│                 │
│ id (PK)        │
│ verb           │
│ particle       │
│ separable (bool│)
│ definition     │
└─────────────────┘
```

### 4.2 Entity Details

**Source**
- `id`: UUID, primary key
- `title`: String, not null — name of the movie, book, series, etc.
- `type`: Enum (`movie`, `tv_series`, `book`, `script`, `other`)
- `author`: String, nullable — author/director/creator
- `year`: Integer, nullable
- `metadata`: JSONB — flexible field for episode numbers, ISBN, genre, etc.
- `created_at`: Timestamp

**Passage**
- `id`: UUID, primary key
- `source_id`: FK → Source
- `text`: Text, not null — the raw passage text
- `start_pos`: Integer — character offset in original source
- `end_pos`: Integer — character offset end
- `location_label`: String — human-readable location (e.g., "Chapter 3", "S02E05 @ 00:12:34")
- `tokens`: JSONB — tokenized form of the passage
- `lemmas`: JSONB — lemmatized tokens

**PassageEmbedding**
- `passage_id`: FK → Passage (one-to-one)
- `embedding`: Vector(384) — dimensionality depends on model

**LemmaIndex**
- `lemma`: String, indexed
- `passage_id`: FK → Passage
- `positions`: JSONB — token positions within the passage where this lemma appears

**Idiom**
- `id`: Integer, primary key
- `canonical_form`: String — e.g., "kick the bucket"
- `lemma_pattern`: String — e.g., "kick the bucket" (lemmatized)
- `definition`: String, nullable

**PhrasalVerb**
- `id`: Integer, primary key
- `verb`: String — base verb, e.g., "give"
- `particle`: String — e.g., "up"
- `separable`: Boolean
- `definition`: String, nullable

**Collocation**
- `id`: Integer, primary key
- `word1`: String, indexed
- `word2`: String, indexed
- `pmi_score`: Float — pointwise mutual information
- `frequency`: Integer — raw co-occurrence count in corpus
- Unique constraint on (`word1`, `word2`)

### 4.3 Indexes

- `Source`: index on `type`, `title`
- `Passage`: index on `source_id`; GIN index on `lemmas`; full-text index (`tsvector`) on `text`
- `LemmaIndex`: B-tree index on `lemma`
- `Collocation`: B-tree index on `word1`, `word2`
- `PassageEmbedding`: HNSW or IVFFlat index on `embedding` (if using pgvector)

---

## 5. Data Flow

### 5.1 Ingestion Flow

```
Raw File (txt/srt/pdf/epub)
  │
  ▼
File Parser (extract text + metadata)
  │
  ▼
Chunker (split into passages of ~3-5 sentences)
  │
  ▼
NLP Pipeline (tokenize → lemmatize → POS tag)
  │
  ├──▶ Store passage + tokens + lemmas → PostgreSQL
  ├──▶ Build lemma index entries → LemmaIndex table
  ├──▶ Generate embedding → Vector Store
  └──▶ Compute co-occurrence stats → Collocation table (batch, post-ingestion)
```

### 5.2 Search Flow — Exact Match

```
User query: "running"
  │
  ▼
Lemmatize query → "run"
  │
  ▼
Query LemmaIndex for lemma = "run"
  │  + PostgreSQL full-text search as fallback
  │
  ▼
Retrieve matching Passages
  │
  ▼
Highlight match positions in text
  │
  ▼
Attach Source metadata + location
  │
  ▼
Return results with context window
```

### 5.3 Search Flow — Semantic Search

```
User query: "anger"
  │
  ▼
Embed query → vector (384 dimensions)
  │
  ▼
Nearest-neighbor search in Vector Store (top-K, cosine similarity)
  │
  ▼
Filter by similarity threshold
  │
  ▼
Retrieve matching Passages from PostgreSQL (by passage_id)
  │
  ▼
Attach Source metadata + location
  │
  ▼
Return results ranked by similarity
```

### 5.4 Search Flow — Multi-Word Expression

```
User query: "kick the bucket"
  │
  ▼
Check Idiom lexicon → match found
  │
  ▼
Generate pattern variants:
  - "kick the bucket", "kicked the bucket", "kicks the bucket", "kicking the bucket"
  │
  ▼
Search passages for pattern variants (regex or lemma-sequence matching)
  │
  ▼
Return results with source + location

---

User query: "give up" (phrasal verb)
  │
  ▼
Check PhrasalVerb table → verb="give", particle="up", separable=true
  │
  ▼
Generate search patterns:
  - "give up", "gave up", "giving up", "given up"
  - Separated: "give .{1,30} up" (regex for split constructions)
  │
  ▼
Search passages
  │
  ▼
Return results

---

User query: "decision" (collocation lookup)
  │
  ▼
Query Collocation table for word1="decision" OR word2="decision"
  │
  ▼
Return top collocates ranked by PMI: make, reach, final, important ...
  │
  ▼
Optionally search for each collocation's occurrences in corpus
```

---

## 6. Implementation Phases

### Phase 1 — MVP (Core Search)

**Goal:** Working end-to-end search with exact match and basic semantic search on a small corpus.

**Features:**
- Ingestion pipeline for plain text and SRT files
- Basic NLP pipeline (tokenization, lemmatization via spaCy)
- Exact match search with lemma normalization
- Semantic search with sentence-transformers + ChromaDB
- REST API with `/api/search` and `/api/sources` endpoints
- CLI or minimal web UI for testing queries
- Results include: matched text, source, location, context window

**Components involved:**
- Ingestion Pipeline (text + SRT parsers only)
- NLP Pipeline
- Exact Match Engine
- Semantic Search Engine
- Search Orchestrator (basic routing)
- API Layer
- Data Access Layer + PostgreSQL + ChromaDB

**Dependencies:**
- Python environment with spaCy, sentence-transformers, FastAPI
- PostgreSQL instance
- ChromaDB instance (can run embedded)
- A small test corpus (5–10 transcripts/books)

---

### Phase 2 — Multi-Word Expressions & Expanded Ingestion

**Goal:** Add idiom, phrasal verb, and collocation detection. Support more input formats.

**Features:**
- Idiom detection with precompiled lexicon + variant matching
- Phrasal verb detection with particle separation handling
- Collocation statistics computation (PMI) and collocation search
- Additional file parsers: PDF, EPUB
- Improved chunking strategy (overlapping windows)
- Search filters: by source type, by source title, by year
- Pagination of search results

**Components involved:**
- MWE Engine (all three sub-modules)
- Ingestion Pipeline (new parsers)
- Search Orchestrator (extended routing + filtering)
- API Layer (new endpoints: `/api/collocations/{word}`)

**Dependencies:**
- Idiom lexicon dataset (e.g., Wiktionary extract, curated JSON)
- Phrasal verb dictionary
- Phase 1 complete and stable

---

### Phase 3 — Production Readiness

**Goal:** Harden the system for larger corpora, improve performance, and add operational tooling.

**Features:**
- Migrate vector store to pgvector (unified database)
- Background job queue for ingestion (Celery + Redis)
- Caching layer for frequent queries (Redis)
- Hybrid search: combine exact match + semantic results with score fusion
- Source management: update, delete sources and re-index
- Logging, monitoring, error handling
- Rate limiting on API
- Docker Compose setup for full-stack deployment
- Web UI (if desired)

**Components involved:**
- All components (hardening + optimization)
- New: Caching layer, Job queue, Monitoring

**Dependencies:**
- Phase 2 complete
- Redis instance
- Docker environment

---

## 7. Testing Strategy

### 7.1 Unit Tests

- **NLP Pipeline:** Verify lemmatization produces correct forms ("running" → "run", "went" → "go"), POS tagging accuracy on known sentences
- **Chunker:** Verify passage boundaries respect sentence limits, correct overlap behavior
- **Idiom detector:** Pattern matching against known idioms with variations
- **Phrasal verb detector:** Particle separation detection, conjugation handling
- **Collocation scoring:** PMI computation correctness
- **Search engines:** Query construction, result formatting, threshold filtering

**Tools:** pytest, pytest-cov

### 7.2 Integration Tests

- **Ingestion → Database:** Ingest a sample file, verify passages, lemma indexes, and embeddings are correctly stored
- **Search → Database:** Seed DB with known passages, execute queries, verify expected passages are returned
- **API → Search Orchestrator:** Send HTTP requests, verify response schema and status codes
- **MWE Engine → Corpus:** Seed corpus with known idiom/phrasal verb occurrences, verify retrieval

**Tools:** pytest + httpx (async test client for FastAPI), test database (PostgreSQL in Docker)

### 7.3 End-to-End Tests

- **Full ingestion + search cycle:** Upload a source file via API → search for known content → verify results
- **Semantic search quality:** Use a curated set of query-expected result pairs to measure recall
- **Multi-word expression retrieval:** Verify idioms with variations, separated phrasal verbs, and collocations all return correct results
- **Edge cases:** Empty queries, very long queries, special characters, queries with no results

**Tools:** pytest, or Playwright/Cypress if a web UI is built

### 7.4 Suggested Coverage Areas

| Area                         | Priority |
|------------------------------|----------|
| Lemmatization correctness    | High     |
| Exact match retrieval        | High     |
| Semantic search relevance    | High     |
| Idiom variant matching       | High     |
| Phrasal verb separation      | Medium   |
| Collocation PMI computation  | Medium   |
| Ingestion pipeline (parsing) | High     |
| API request validation       | Medium   |
| Concurrent ingestion jobs    | Low (Phase 3) |

---

## 8. Risks and Design Considerations

### 8.1 Architectural Risks

- **Embedding model lock-in:** Changing the embedding model later requires re-embedding the entire corpus. *Mitigation:* Store the model name/version alongside embeddings; build a re-indexing pipeline early.
- **Chunk size sensitivity:** Too-small chunks lose context; too-large chunks dilute relevance. *Mitigation:* Make chunk size configurable; experiment with overlapping windows.
- **MWE lexicon coverage:** Precompiled idiom/phrasal verb lists will never be complete. *Mitigation:* Supplement lexicon-based matching with semantic fallback detection; allow users to contribute new entries.

### 8.2 Scalability Considerations

- **Corpus growth:** As the corpus grows, full-table scans become infeasible. *Mitigation:* Ensure all search paths use indexes (full-text, B-tree, HNSW for vectors). Benchmark with 100K+ passages early.
- **Embedding generation throughput:** Generating embeddings for a large corpus is CPU/GPU intensive. *Mitigation:* Use batched embedding generation; consider GPU acceleration; make ingestion asynchronous.
- **Vector search latency:** Nearest-neighbor search slows with corpus size. *Mitigation:* Use approximate NN indexes (HNSW); apply pre-filters (source type, year) to reduce search space.
- **Collocation table size:** With a large vocabulary, the collocation table can grow quadratically. *Mitigation:* Only store pairs above a minimum frequency threshold and PMI cutoff.

### 8.3 Security Concerns

- **Input sanitization:** User queries must be sanitized before constructing SQL or regex patterns. Use parameterized queries exclusively; never interpolate user input into SQL.
- **File upload validation:** Ingestion endpoints accept file uploads — validate file types, enforce size limits, and scan for malformed input that could crash parsers.
- **Rate limiting:** Semantic search is computationally expensive. Apply rate limiting to prevent abuse or accidental DoS.
- **Data licensing:** The corpus may contain copyrighted material. This is a legal/policy concern rather than a technical one, but the system should track source provenance via metadata.
- **API authentication:** Even for internal use, add basic API key authentication to prevent unauthorized access to search and ingestion endpoints.
