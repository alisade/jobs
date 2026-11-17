// q5 suppliers_in_country
// params: $tenant_id, $country (ISO 3166 alpha-2, the Facility's country)
// returns: one column, the distinct names of suppliers located in a facility in that country
MATCH (s:Supplier {tenant_id: $tenant_id})-[:LOCATED_IN]->(f:Facility {tenant_id: $tenant_id, country: $country})
RETURN DISTINCT s.name
ORDER BY s.name
