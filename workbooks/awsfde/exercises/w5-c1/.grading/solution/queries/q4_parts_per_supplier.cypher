// q4 parts_per_supplier (aggregation)
// params: $tenant_id
// returns: two columns, supplier name and the number of parts it supplies
MATCH (s:Supplier {tenant_id: $tenant_id})-[:SUPPLIES]->(p:Part {tenant_id: $tenant_id})
RETURN s.name AS supplier, COUNT(p) AS parts
