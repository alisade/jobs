"""Settings (given). In production the key comes from Secret Manager; never hard-code a real key."""

import os

DEID_KEY = os.environ.get("KHP_DEID_KEY", "test-only-key-not-a-secret").encode()
AS_OF_YEAR = 2026
