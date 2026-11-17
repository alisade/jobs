// Hand-written types for the catalog API (prototype). Replace with the generated file: make contract.
export interface Product {
  sku: string;
  name: string;
  category: string;
  price: number;
}

export interface ProductList {
  products: Product[];
  page: number;
}
