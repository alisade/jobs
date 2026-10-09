# Reference: ms/w6-c1

Reference code: `.grading/solution/src/Tailspin.Plugins/*.cs` and `.grading/solution/registration/*.json`.

## Key decisions

- **PreOperation (20), synchronous.** The plug-in changes values on the message (`Target`), which Learn
  says belongs in PreOperation: it runs inside the transaction before the main operation, so the stamped
  columns are written in the same database write. PostOperation would require a second `Update`, which
  re-enters the pipeline (a new Update event) and costs a second write. PreValidation would also work for
  the rejection part and is cheaper for cancellations (outside the transaction, before security checks),
  but the stamping belongs in PreOperation; one step keeps it simple. A strong answer mentions splitting
  validation into PreValidation if rejections were frequent.
- **Stage guard throws.** If someone registers the step on PostOperation the Target assignments are
  silently ignored. Throwing makes the misregistration visible in the first test.
- **Pre-image, not Retrieve.** Images are the documented performance practice. Only
  `contoso_status`, `contoso_actualstart`, `contoso_resolutionnotes` are read, so only those are in the
  image. A missing image is a deployment bug, reported as such.
- **Filtering attribute `contoso_status` only.** The logic only cares about status changes. Never include
  the primary key: it is always present on Update and negates the filter. Filtering attributes fire even
  if the value is unchanged, hence the same-status no-op.
- **No Depth guard.** The `IExecutionContext.Depth` docs say not to build business logic on Depth; a
  Depth > 1 skip would let flows and other plug-ins bypass validation, which is exactly the incident.
- **Custom API = Action, Global, None.** The Dataverse connector in Power Automate only performs actions,
  so a Function is not callable from the flow. Unbound -> Global. "Must not be changed or cancelled by
  others" -> AllowedCustomProcessingStepType None. Functions must also have at least one response property
  and are GET-only with a URL length limit; none of that matters once the flow requirement rules them out.
  Before shipping: managed solution, Is Customizable = false, consider IsPrivate.
- **Main operation stage 30.** The custom API plug-in runs in MainOperation; it is not registered as a step.

## Interview angles

- What happens to the transaction if the PreOperation plug-in throws? (Whole operation rolls back; Learn
  recommends cancelling in PreValidation where possible because a rollback in PreOperation is costly.)
- How would you unit-test this without FakeXrmEasy? (Hand-rolled IServiceProvider + RemoteExecutionContext,
  as in the tests.)
- How do you version and ship this assembly? (Solution, build/revision bump for in-place upgrade; major/minor
  bump creates a new assembly registration.)
