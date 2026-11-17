# Constraints from security and platform review

1. **Approved egress only.** Calls to external model providers must leave through the egress proxy, to
   allow-listed hostnames, with credentials from the secrets manager. No provider API keys in front-end
   code or in the associate app.
2. **Two providers approved.** Provider A (primary, best quality on the eval set) and provider B
   (fallback, about 30 percent cheaper, slightly lower quality, different API shape). Both are under
   data processing agreements with zero data retention.
3. **PII.** Customer names, emails, addresses and payment data must not be sent to a model. Order ids and
   SKUs are fine. Logs that contain prompts are retained 30 days, access-controlled.
4. **Least privilege.** The assistant acts with the end user's identity: a shopper can only see their own
   orders; an associate only their store's orders. No service-wide "god" token for order data.
5. **Write actions** (start_return) require explicit user confirmation and are audited.
6. **Platform.** New services run on the shared EKS clusters with the standard Helm chart, OpenTelemetry
   SDK, and Kong routes. Platform will not run a new stateful datastore for one team in Q4; Redis
   (managed) is available.
7. **Change freeze.** Orders team has a Q4 change window once a month; anything that needs an orders-db
   change or a new order-service endpoint must be ready for the 2026-12-02 window or wait until January.
