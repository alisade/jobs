# assistant releases

## 2026.11.07 (deployed 2026-11-07 15:10 PT)
- search_products now includes up to 3 recent reviews per product, so the assistant can say what customers
  think ("people love the two doors"). Reviews are added to the product record the model sees.

## 2026.11.09 (deployed 2026-11-09 06:05 PT)
- Model version upgrade (same model family, newer snapshot). Eval suite: 412/415 vs 410/415 before.
- No prompt or tool changes.

## 2026.10.20
- Output grounding check (grounding.py): every price, promo code and percent in an answer must be found
  in the tool results, otherwise the customer gets a safe fallback answer.
