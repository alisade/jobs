# ms/w7-c1 answer (model)

## Approach
State is three things: the last known value (what the platform has, or what we last committed), the
pending debounce timer, and the current prefix/debounce config. Handlers are stored as readonly arrow
properties so `destroy` can remove exactly the same function references. All config and disabled state is
applied in one `applyContext` used by both `init` and `updateView`, so the two paths cannot drift.

## Fix
- Manifest: added `tagPrefix` and `debounceMs` as `usage="input"` properties and the `css` resource.
- Commits go through one `setValue` that compares with the last known value before calling
  `notifyOutputChanged`, so re-typing the stored value, platform round-trips and `updateView` never echo.
- `input` events debounce; `blur` commits immediately and clears the timer.
- Invalid text toggles `tsp-invalid` and shows a `role="alert"` message; the output keeps the last valid value.
- `destroy` clears the timer, removes both listeners and removes the root element.
- Verified with `make test` and the hidden-style cases (fake timers for debounce and leak checks).

## Trade-offs / what I would do in production
- Client validation is UX, not integrity: the same rule belongs server-side (a PreOperation plug-in or a
  column-level business rule) because imports, flows and the Web API bypass the control.
- Debounce trades write latency for fewer `OnChange` events; blur flush covers save-without-tabbing.
- For a richer UI I would use a virtual (React/Fluent) control to share the platform React and reduce bundle size.
- Ship in a solution with a version bump per change; test in the PCF harness and on a real form.
