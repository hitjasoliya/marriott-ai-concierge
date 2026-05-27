# Marriott AI Hotel Concierge

Conversational AI hotel assistant specializing in Marriott properties. Hybrid retrieval pipeline combining SQL + PostGIS geo-search + pgvector semantic reranking + LLM intent extraction.

## Architecture

```
User Query
  ↓
Gemini Intent Extraction  →  city, landmark, semantic_intent, amenities, dates
  ↓
Nominatim Landmark Resolution  →  "Taj Mahal" → (27.1751, 78.0421)
  ↓
SQL + JSONB Filtering  →  city, hotel_type, price range, amenities
  ↓
PostGIS Geo Search  →  ST_DWithin radius, distance scoring
  ↓
pgvector Semantic Rerank  →  BGE-small cosine similarity on candidate pool
  ↓
Weighted Ranking  →  0.45×semantic + 0.25×distance + 0.20×rating + 0.10×availability
  ↓
Gemini Streaming Response  →  SSE to frontend
```

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy (async), PostgreSQL + PostGIS + pgvector
- **Embeddings**: BAAI/bge-small-en-v1.5 via sentence-transformers (384-dim, local inference)
- **LLM**: Google Gemini 2.0 Flash (intent extraction + response generation)
- **Frontend**: Next.js 16, React 19, TypeScript, TailwindCSS v4, App Router
- **Infrastructure**: Docker Compose

## Setup

### Prerequisites
- Docker + Docker Compose
- Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

### Quick Start

1. Copy environment file:
```bash
cp .env.example .env
```

2. Edit `.env` — add your `GEMINI_API_KEY` and optionally your email for `NOMINATIM_EMAIL`.

3. Start all services:
```bash
make dev
```
This builds and starts PostgreSQL, backend (port 8000), and frontend (port 3000).

4. Seed the database with 70 Marriott hotels:
```bash
make seed
```
This inserts hotels and computes embeddings. The BGE model downloads on first run and caches to a Docker volume.

5. Open http://localhost:3000 and start searching.

### Commands

| Command | Description |
|---------|-------------|
| `make dev` | Build and start all services |
| `make seed` | Seed database with 70 hotels + embeddings |
| `make embed` | Recompute all hotel embeddings |
| `make reset` | Tear down volumes and rebuild |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/search` | Main search endpoint (SSE streaming) |
| `GET` | `/hotel/{id}` | Hotel details |
| `GET` | `/availability?hotel_id=&check_in=&check_out=&guests=` | Check availability |
| `POST` | `/seed-hotels` | Trigger seeding |
| `POST` | `/embed-hotels` | Trigger re-embedding |
| `GET` | `/health` | Health check |

### SSE Events

The `/search` endpoint streams these events:
- `status` — progress updates
- `intent` — extracted search intent
- `hotels` — top 5 ranked hotel results
- `token` — Gemini response tokens (streaming)
- `done` — stream complete
- `error` — error message

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `DATABASE_URL` | No | `postgresql+asyncpg://marriott:password@postgres:5432/marriott_hotels` | PostgreSQL connection |
| `EMBEDDING_MODEL` | No | `BAAI/bge-small-en-v1.5` | HuggingFace embedding model |
| `RANKING_WEIGHTS_JSON` | No | `{"semantic":0.45,"distance":0.25,"rating":0.20,"availability":0.10}` | Ranking weights |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend URL for frontend |
| `NOMINATIM_EMAIL` | No | `user@example.com` | Email for Nominatim User-Agent |

## Seed Data

70 hand-crafted Marriott hotel records across 10 cities:

| City | Hotels |
|------|--------|
| Mumbai | 8 |
| Delhi | 8 |
| Agra | 5 |
| Goa | 8 |
| Bangalore | 7 |
| Jaipur | 5 |
| Dubai | 8 |
| Singapore | 7 |
| London | 7 |
| New York | 7 |

Brands: JW Marriott, Marriott Marquis, Marriott Hotels, Renaissance, Sheraton, Westin, W Hotels, Courtyard by Marriott, Fairfield by Marriott, The Ritz-Carlton.
