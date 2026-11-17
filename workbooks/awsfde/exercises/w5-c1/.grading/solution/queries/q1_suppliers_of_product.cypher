// q1 suppliers_of_product (multi-hop)
// params: $tenant_id, $product (Product.name)
// returns: one column, the distinct supplier names that supply a part used in the product
MATCH (s:Supplier {tenant_id: $tenant_id})-[:SUPPLIES]->(p:Part {tenant_id: $tenant_id})-[:USED_IN]->(x:Product {tenant_id: $tenant_id, name: $product})
RETURN DISTINCT s.name
ORDER BY s.name
