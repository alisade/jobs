// q1 suppliers_of_product (multi-hop)
// params: $tenant_id, $product (Product.name)
// returns: one column, the distinct supplier names that supply a part used in the product
// Draft from the prototype notebook. It answers the question but is not tenant-safe yet.
MATCH (s:Supplier)-[:SUPPLIES]->(p:Part)-[:USED_IN]->(x:Product {name: $product})
RETURN s.name
