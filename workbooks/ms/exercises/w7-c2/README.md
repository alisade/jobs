# ms/w7-c2: Custom connector for the Contoso Parts API

Type: coding. Estimate: 1.5-2 h. Exam: AB-400 - Develop integrations (10-15%): custom connectors;
also Extend the platform (35-40%): connectors used by flows and agents.

## Scenario

Contoso Field Engineering runs its spare-parts system behind an Azure Function app
(`contoso-parts-func.azurewebsites.net`, routes under `/api`). Technicians need to look up parts and
raise reorders from a canvas app, a cloud flow and the "Field Assist" Copilot Studio agent. A
contractor hand-wrote a first connector definition in `connector/`. Security review rejected it
(function key in every connection, a client secret committed to the repo), makers complain that
they have to type warehouse codes from memory, and the list action only ever returns the first
100 parts.

The Function app now sits behind App Service authentication with Entra ID. Its app registration
exposes the App ID URI `api://contoso-parts-api`; the connector's own app registration has client id
`3f9c2a71-6b1e-4d8a-9c55-0e7f1b2d4a60`. The backend also requires every Power Platform call to
carry the header `x-contoso-caller: power-platform`.

## Your task

Fix and complete `connector/apiDefinition.swagger.json` and `connector/apiProperties.json`
(the two files `paconn` and the custom connector wizard use):

1. Valid OpenAPI 2.0 with a bare `host`, `basePath` `/api`, HTTPS only.
2. Five operations with PascalCase operation ids: `ListParts`, `GetPart`, `CreateReorder`, and the
   helper operations `ListWarehouses` (`GET /warehouses`) and `ListCategories` (`GET /categories`,
   returns `{"value": [{"code": "...", "displayName": "..."}]}`). Helpers are hidden from makers.
3. Entra ID authentication: an `oauth2` (accessCode) security definition and an `aad` connection
   parameter with LoginUri, TenantId and ResourceUri; no secret in the files; per-connector
   redirect URI.
4. Maker experience: summaries (80 chars max, alphanumeric and parentheses only) and sentence
   descriptions on every operation, `x-ms-summary` and `description` on every parameter,
   `x-ms-summary` on every response property, deliberate `x-ms-visibility`.
5. Dropdowns: `warehouseCode` in the reorder body and the `category` query parameter use
   `x-ms-dynamic-values` backed by the helper operations.
6. Paging: `ListParts` is pageable (`x-ms-pageable`) and its response carries the next-page link.
7. Required internal parameters (`api-version`) need a default.
8. Responses: exact schemas for success responses (the 201 from `CreateReorder` returns the reorder),
   no schema on `default` responses.
9. A `setheader` policy template instance that sets `x-contoso-caller: power-platform` on every
   request (override if present).
10. A brand colour that is not white or the default `#007ee5`; publisher and stackOwner set.

## Acceptance criteria

- `make test` passes (validity, host/basePath/schemes, operation ids, aad).
- The hidden checks for items 1-10 pass. They follow the rules in the custom connector docs, the
  certification requirements and the swagger validator rule list linked below.
- `ANSWER.md` explains the auth design and the ALM plan for the connector.

## How to run

```
make setup     # uv sync (installs pytest and openapi-spec-validator)
make test
```

Then from the workbooks root: `/grade ms/w7-c2`. There is no live tenant here; if you have a dev
environment you can optionally try `paconn create` / `pac connector create` with these files.

## What to submit

- `connector/apiDefinition.swagger.json`, `connector/apiProperties.json`
- `ANSWER.md`

## Study guide links

- [Study plan Week 7 weekend - Custom connectors](../../../../microsoft-adf-powerapps-study-plan.html#week7)
- [Create a custom connector from an OpenAPI definition](https://learn.microsoft.com/en-us/connectors/custom-connectors/define-openapi-definition)
- [OpenAPI extensions for custom connectors](https://learn.microsoft.com/en-us/connectors/custom-connectors/openapi-extensions)
- [Policy templates](https://learn.microsoft.com/en-us/connectors/custom-connectors/policy-templates) / [Set HTTP header](https://learn.microsoft.com/en-us/connectors/custom-connectors/policy-templates/setheader/setheader)
- [Certification requirements (connection parameters, strings)](https://learn.microsoft.com/en-us/connectors/custom-connectors/certification-submission)
- [Swagger validator rules](https://learn.microsoft.com/en-us/connectors/custom-connectors/certification-swagger-validator-rules)
- [Use connectors as tools in Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-connectors)
