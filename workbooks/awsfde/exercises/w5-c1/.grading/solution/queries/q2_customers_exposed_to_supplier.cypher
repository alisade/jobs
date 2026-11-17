// q2 customers_exposed_to_supplier (multi-hop, 3 relationships)
// params: $tenant_id, $supplier (Supplier.name)
// returns: one column, the distinct customer names that ordered a product containing a part from that supplier
MATCH (s:Supplier {tenant_id: $tenant_id, name: $supplier})-[:SUPPLIES]->(p:Part {tenant_id: $tenant_id})-[:USED_IN]->(x:Product {tenant_id: $tenant_id})<-[:ORDERED]-(c:Customer {tenant_id: $tenant_id})
RETURN DISTINCT c.name
ORDER BY c.name
