# Reference: ms/w7-c2 Contoso Parts custom connector

Files: `.grading/solution/connector/apiDefinition.swagger.json` and `apiProperties.json`.

## What was wrong in the starter, and the fix

| Problem | Why it matters | Fix |
|---|---|---|
| `host` had a scheme and path, `basePath` lacked the leading `/`, `schemes` allowed http | Swagger validator rules HostNameNotValid / BasePathNotValid; plain HTTP is not acceptable | `host: contoso-parts-func.azurewebsites.net`, `basePath: /api`, `schemes: [https]` |
| Function key (`apiKey` in `x-functions-key`) | Shared secret in every connection, no user identity, no Conditional Access | `oauth2` accessCode security definition + `identityProvider: aad` in apiProperties with `ResourceUri` = the Function's App ID URI; protect the Function with App Service authentication (Easy Auth) and validate audience/scope |
| `clientSecret` committed in apiProperties.json | Secrets are entered in the wizard / via `paconn` at create time and are never exported | Remove it; rotate the leaked secret |
| Generic `oauth2` provider with v2 authorize/token URLs, `redirectMode: Global` | Works, but loses Entra-specific behaviour; the per-connector redirect URI is enforced for OAuth custom connectors (connectors on the old global redirect URI stopped working for new connections after February 2024) | `aad` provider with LoginUri/TenantId/ResourceUri; `redirectMode: GlobalPerConnector` and register the per-connector redirect URI on the app registration |
| `operationId` values with spaces / camelCase | Operation ids become action names in flows and canvas apps; spaces break references | `ListParts`, `GetPart`, `CreateReorder`, `ListWarehouses`, `ListCategories` |
| No `x-ms-pageable` and the next-link property named `next` | Flow pagination cannot follow pages; validator rule InvalidNextLinkNameValue accepts only `nextLink` or `@odata.nextLink` | `x-ms-pageable: {nextLinkName: nextLink}` and a `nextLink` property in the 200 schema |
| `api-version` internal + required without default | Internal parameters are hidden, so the maker can never set it: calls fail | `default: 2026-09-01` |
| Free-text warehouse and category | Makers and agents guess codes | `x-ms-dynamic-values` against internal `ListWarehouses` / `ListCategories` (`value-collection`, `value-path`, `value-title`) |
| `default` response with a schema, 201 without schema | Certification: exact schemas for expected responses only; without a 201 schema there is no dynamic content | 201 returns `Reorder`; error codes documented without schemas |
| Missing x-ms-summary / descriptions, 140-char summary | Poor designer UI, poor tool selection when the connector is a Copilot Studio tool | Title-case `x-ms-summary`, sentence `description`, summary <= 80 chars |
| No policy for the caller header | Backend requires `x-contoso-caller` to route and meter Power Platform traffic | `setheader` policy template, Request section, existsAction `override` |
| `iconBrandColor` `#007ee5` | Default colour is rejected for certification | Brand colour |

## Notes

- Custom connectors require OpenAPI 2.0; OpenAPI 3 must be converted.
- In a solution, the connector travels with connection references; use environment variables for
  the host when environments point at different backends.
- When the connector is used as a tool in Copilot Studio, the operation summary and description
  and parameter descriptions are what the orchestrator reads. Write them for that reader.

## Interview angles

- Why OAuth with the user's identity rather than a function key? (Auditing, Conditional Access,
  per-user authorization in the backend, key rotation.)
- When would you use custom code (C# script) instead of a policy template? (Payload transforms
  the templates cannot express; mind the execution time limit.)
