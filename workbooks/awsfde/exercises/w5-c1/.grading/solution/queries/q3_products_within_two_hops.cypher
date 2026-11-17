// q3 products_within_two_hops (variable-length path)
// params: $tenant_id, $supplier (Supplier.name)
// returns: one column, the distinct product names reachable from the supplier in 1 or 2 hops
MATCH (s:Supplier {tenant_id: $tenant_id, name: $supplier})-[*1..2]->(x:Product {tenant_id: $tenant_id})
RETURN DISTINCT x.name
ORDER BY x.name
