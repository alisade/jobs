# Cleaned up from generated.tf (terraform plan -generate-config-out) in PR #418.
resource "google_compute_network" "riq_legacy" {
  name         = "riq-legacy"
  project      = "tsl-riq-prod"
  description  = "RIQ legacy VPC (hand-built 2023)"
  routing_mode = "GLOBAL"
}

resource "google_compute_subnetwork" "riq_usc1" {
  name                     = "riq-usc1"
  project                  = "tsl-riq-prod"
  region                   = "us-central1"
  network                  = google_compute_network.riq_legacy.id
  ip_cidr_range            = "10.40.0.0/20"
  private_ip_google_access = true
}

resource "google_compute_subnetwork" "riq_use4" {
  name                     = "riq-use4"
  project                  = "tsl-riq-prod"
  region                   = "us-east4"
  network                  = google_compute_network.riq_legacy.id
  ip_cidr_range            = "10.40.16.0/20"
  private_ip_google_access = true
}
