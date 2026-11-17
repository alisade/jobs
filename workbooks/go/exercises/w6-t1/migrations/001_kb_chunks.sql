-- 001: chunk store for the knowledge base (pgvector 0.8.0, Postgres 16, RDS)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE kb_chunks (
    id          bigserial PRIMARY KEY,
    tenant_id   text        NOT NULL,
    collection  text        NOT NULL,
    doc_id      text        NOT NULL,
    chunk_no    int         NOT NULL,
    content     text        NOT NULL,
    embedding   vector(1024) NOT NULL,   -- voyage-3, L2-normalised
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, doc_id, chunk_no)
);

CREATE INDEX kb_chunks_tenant_collection_idx ON kb_chunks (tenant_id, collection);
