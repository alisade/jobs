resource "google_storage_bucket" "riq_exports" {
  name     = "tsl-riq-exports"
  project  = "tsl-riq-prod"
  location = "US-CENTRAL1"
  labels = {
    owner = "riq"
    env   = "prod"
  }
}

resource "google_sql_database_instance" "riq_legacy_pg" {
  name             = "riq-legacy-pg"
  project          = "tsl-riq-prod"
  region           = "us-central1"
  database_version = "POSTGRES_14"
  settings {
    tier              = "db-custom-4-16384"
    availability_type = "REGIONAL"
  }

  lifecycle {
    prevent_destroy = true
  }
}
