# __generated__ by Terraform (terraform plan -generate-config-out=generated.tf), 2026-11-10
# Please review these resources and move them into your main configuration files.

# __generated__ by Terraform from "projects/tsl-riq-prod/global/networks/riq-legacy"
resource "google_compute_network" "riq_legacy" {
  auto_create_subnetworks                   = false
  delete_default_routes_on_create           = false
  description                               = "RIQ legacy VPC (hand-built 2023)"
  enable_ula_internal_ipv6                  = false
  internal_ipv6_range                       = null
  mtu                                       = 1460
  name                                      = "riq-legacy"
  network_firewall_policy_enforcement_order = "AFTER_CLASSIC_FIREWALL"
  project                                   = "tsl-riq-prod"
  routing_mode                              = "GLOBAL"
}

# __generated__ by Terraform from "tsl-riq-prod/tsl-riq-exports"
resource "google_storage_bucket" "riq_exports" {
  default_event_based_hold    = false
  enable_object_retention     = false
  force_destroy               = false
  labels                      = { env = "prod", owner = "riq" }
  location                    = "US-CENTRAL1"
  name                        = "tsl-riq-exports"
  project                     = "tsl-riq-prod"
  public_access_prevention    = "enforced"
  requester_pays              = false
  rpo                         = null
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
}
# (subnetworks and the SQL instance omitted from this excerpt)
