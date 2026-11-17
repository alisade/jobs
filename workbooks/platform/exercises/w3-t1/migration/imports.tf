# Import batch 07: RIQ legacy network, exports bucket and the legacy Postgres instance (OPS-7702).
import {
  to = google_compute_network.riq_legacy
  id = "projects/tsl-riq-prod/global/networks/riq-legacy"
}

import {
  to = google_compute_subnetwork.riq_usc1
  id = "projects/tsl-riq-prod/regions/us-central1/subnetworks/riq-usc1"
}

import {
  to = google_compute_subnetwork.riq_use4
  id = "projects/tsl-riq-prod/regions/us-east4/subnetworks/riq-use4"
}

import {
  to = google_storage_bucket.riq_exports
  id = "tsl-riq-prod/tsl-riq-exports"
}

import {
  to = google_sql_database_instance.riq_legacy_pg
  id = "projects/tsl-riq-prod/instances/riq-legacy-pg"
}
