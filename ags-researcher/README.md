# AGS Researcher

Cross-cutting multi-source research agent (Faza 0.5, Opcja A — kaskada kosztowa).
Hub-and-Spoke async: **Python worker = orkiestracja** (poll `research_jobs` przez `FOR UPDATE SKIP LOCKED`); **n8n = adaptery 5 źródeł + ingress + status polling**. Synteza Sonnet 4.6 → 4 strategie decyzji. READ-ONLY (zero write-capable MCP).

## Status build (23-25/06/2026)
- [x] DDL: 9 tabel live w `ags_crd` (3 Phase 0-lite + 6 Researcher). `db/001_init.sql`.
- [x] vector add-on zaaplikowany 23/06 (pgvector 0.8.2 live, `query_embedding VECTOR(1536)` + indeks hnsw). Semantic cache READY (`SEMANTIC_CACHE_ENABLED=true`).
- [x] Szkielet repo (ten katalog).
- [x] 6 modułów Python (router, cache, budget, prompts, synth, failure, sources).
- [x] Worker loop + FastAPI /health /metrics (py_compile clean).
- [ ] Day 3: 6 workflowów n8n (5 adapterów + ingress/callback) + status-adaptery + testy integracyjne.
- [ ] Brama 3 acceptance → LIVE cel 25/06.

## Deploy (Mikrus, potwierdzone 24/06)
Infra: **standalone `docker run`** (BEZ compose). Kontener bazy `pg_n8n` jest na sieci Dockera **`n8n_network`** - worker MUSI wejść na tę sieć, żeby gadać z bazą po `pg_n8n:5432`.
```bash
cp .env.example .env   # uzupełnij (POSTGRES_DSN host = pg_n8n)
docker build -t ags-researcher:latest .
docker run -d --name ags-researcher --restart unless-stopped -m 512m \
  --network n8n_network -p 127.0.0.1:8088:8088 \
  --env-file ./.env -v "$PWD/logs":/app/logs -v "$PWD/cache":/app/cache \
  ags-researcher:latest
curl -fsS http://localhost:8088/health
```

## Migracje
- `db/001_init.sql` — zaaplikowane 23/06 jako `ags_crd_user` (ma CREATE w bazie).
- `db/002_vector_addon.sql` — linia 1 (CREATE EXTENSION) wymaga superusera `n8n`; linie 2-3 robi owner `ags_crd_user`. Idempotentne.
- `db/003_relax_provenance_types.sql` — 26/06: `freshness`->TEXT, `supporting_evidence`/`supporting_claims`->TEXT[] (honest types dla danych ze źródeł i wyjścia LLM, żeby pierwszy job się nie wywalił na cast). Aplikowane jako `ags_crd_user`; tabele puste.
