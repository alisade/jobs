-- 003: ANN index. Built CONCURRENTLY on 2026-08-12 (took 41 min at 600k rows).
-- m/ef_construction chosen from the recall benchmark in KB-198.
CREATE INDEX CONCURRENTLY kb_chunks_embedding_hnsw
    ON kb_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
