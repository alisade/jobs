# Reference: ms/w7-c1

The reference implementation is `.grading/solution/AssetTagInput/index.ts` plus the finished manifest.

Key points an examiner and an interviewer look for:

1. **Lifecycle.** `init` runs once (build DOM, attach handlers, keep `notifyOutputChanged`); `updateView` runs
   after init and whenever the platform changes inputs, size, mode or the bound value. It must render, not
   report: calling `notifyOutputChanged` from `updateView` creates an echo loop (framework calls getOutputs,
   then updateView again). `getOutputs` is pulled by the framework after you notify. `destroy` is where you
   release listeners, timers and subscriptions.
2. **No-op suppression.** Compare with the last known value before notifying. Typing `tsp 123456` when the
   column already holds `TSP-123456` must not dirty the form.
3. **Null handling.** `raw` is `null` for an empty column; returning `undefined` from getOutputs clears it.
4. **Disabled.** `context.mode.isControlDisabled` covers read-only forms and inactive records; field-level
   security surfaces as `parameters.<prop>.security.editable === false`.
5. **Manifest.** `property` elements with `usage="bound"` bind to a column; `usage="input"` are maker
   configuration. `of-type` uses the PCF type names (`SingleLine.Text`, `Whole.None`). `resources` lists
   `code` (exactly one), `css` and `resx`. `feature-usage/uses-feature` is only needed for Device, Utility or
   WebAPI features, which this control does not use. `ManifestTypes.d.ts` is generated from the manifest by
   the build, which is why a missing property shows up as a TypeScript error in a real project.
6. **Escaping.** Build the pattern with an escaped prefix (or avoid regex for the prefix entirely).

Interview angles:
- Why not validate in `getOutputs`? (It is pulled by the framework; validation should gate the notify.)
- Standard vs virtual control: when does React + platform libraries pay off?
- How do you stop the same bad data arriving via the Web API? (Server-side plug-in or business rule.)
