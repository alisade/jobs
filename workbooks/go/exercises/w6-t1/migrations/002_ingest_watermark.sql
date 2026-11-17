-- 002: ingestion watermark per source, used by the KnowledgeBase operator's ingest Job
CREATE TABLE kb_ingest_watermark (
    tenant_id   text        NOT NULL,
    source_uri  text        NOT NULL,
    etag        text        NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, source_uri)
);
