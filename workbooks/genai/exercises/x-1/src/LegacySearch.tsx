// The existing storefront search results (unchanged since 2023). Do not change the markup: the
// merchandising team's analytics depend on it.
import { formatPrice } from "./vendor/events";

export interface LegacyResult {
  sku: string;
  name: string;
  price_cents: number;
}

export type SearchFn = (q: string) => Promise<LegacyResult[]>;

export function LegacyResults({ results }: { results: LegacyResult[] }) {
  if (!results.length) return <p>No products found.</p>;
  return (
    <ul aria-label="Search results">
      {results.map((r) => (
        <li key={r.sku}>
          <a href={`/p/${r.sku}`}>{r.name}</a> {formatPrice(r.price_cents)}
        </li>
      ))}
    </ul>
  );
}
