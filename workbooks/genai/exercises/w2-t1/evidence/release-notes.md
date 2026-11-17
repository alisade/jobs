# catalog-search 2026.11.04 (deployed 2026-11-04 22:40 PT)

- Search results now include a `badge` field with the active promotion for each SKU (PromoHub).
  Uses the vendor's Python SDK `promotions_sdk.PromotionsClient.badges_for(skus)`, one call per search.
- Bumped FastAPI to 0.115.6.
- No schema or index changes.

Deployment: 6 replicas, 1 uvicorn worker per pod (`uvicorn catalog_search.app:app --workers 1`),
liveness probe `GET /healthz` periodSeconds=5 timeoutSeconds=1 failureThreshold=3.
