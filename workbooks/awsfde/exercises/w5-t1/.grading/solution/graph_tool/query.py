"""openCypher template for the suppliers_of_product tool. Parameters: $tenant_id, $product.

Every node is constrained to the caller's tenant, so a path that crosses into another tenant's
vertices (bad data, an id collision) matches nothing. DISTINCT because a supplier of two parts of the
same product would otherwise appear twice.
"""

SUPPLIERS_OF_PRODUCT = (
    "MATCH (s:Supplier {tenant_id: $tenant_id})-[:SUPPLIES]->(p:Part {tenant_id: $tenant_id})"
    "-[:USED_IN]->(x:Product {tenant_id: $tenant_id, name: $product}) "
    "RETURN DISTINCT s.name, s.tenant_id"
)
