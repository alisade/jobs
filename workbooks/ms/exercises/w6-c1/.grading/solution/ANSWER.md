# ms/w6-c1 answer

## Approach
Filled the transition table first and unit-tested IsAllowed, then built the plug-in guard clauses in the
order the pipeline would hit them (message/entity, stage, Target content, image), then the stamping
rules, then the custom API. Tested with the hand-rolled fakes; asserted no IOrganizationService calls.

## Fix
- Status plug-in: PreOperation (20) synchronous on Update of contoso_workorder, filtering attribute
  contoso_status only, pre-image "PreImage" with contoso_status, contoso_actualstart,
  contoso_resolutionnotes. Values are set on Target so they are written by the main operation; no
  second Update, no Retrieve. Wrong stage throws because Target changes after the main operation are
  ignored. No Depth-based skip (flows arrive at Depth 2 and must be validated too).
- Custom API: Action (isFunction false) because the Dataverse connector only performs actions; Global
  binding; AllowedCustomProcessingStepType None so nobody can register sync steps that alter or cancel it.

## Trade-offs / what I would do in production
- If rejections are common, move the pure validation to PreValidation to avoid transaction rollbacks.
- Ship in a managed solution with Is Customizable = false on the custom API; set IsPrivate until the
  contract is stable.
- Plug-in trace log on "Exception" in production; App Insights export for plug-in failures.
- Bump the assembly build/revision for in-place upgrades; keep steps in the solution explicitly.
