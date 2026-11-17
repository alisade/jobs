#!/bin/bash
# Weekly: drop archived claims older than the retention period (7 years) from the yearly archive tables.
set -euo pipefail
YEAR=$(( $(date +%Y) - 8 ))
sqlplus -s "claimdesk_batch/${CLAIMDESK_BATCH_PW}@CLMPRD" <<SQL
DELETE FROM CLMARCH.CLAIM_ARCHIVE_${YEAR} WHERE CLOSED_DATE < ADD_MONTHS(SYSDATE, -84);
COMMIT;
SQL
