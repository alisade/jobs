"""openCypher template for the suppliers_of_product tool. Parameters: $tenant_id, $product."""

SUPPLIERS_OF_PRODUCT = (
    "MATCH (s:Supplier)-[:SUPPLIES]->(p:Part)-[:USED_IN]->(x:Product {tenant_id: $tenant_id, name: $product}) "
    "RETURN s.name, s.tenant_id"
)
