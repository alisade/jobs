# Reference: go/w1-t1 flagd returns 500 on every flag update

## Root cause

Commit `a41c9e2` (v1.14.0) refactored `validate` to collect every field error:

```go
func validate(f Flag) error {
    var verr *ValidationError   // nil pointer
    ...
    return verr                 // converted to error
}
```

An interface value is a (dynamic type, dynamic value) pair. It is `nil` only when **both**
are nil. Returning the nil `*ValidationError` as `error` produces
`(type=*ValidationError, value=nil)`, which is not equal to `nil`. So in `Service.Put`,
`if err := validate(f); err != nil` is true for every flag, valid or not.

The rest of the evidence follows from that:

- `fmt.Errorf("validation failed: %w", err)` formats the nil pointer: fmt calls `Error()`,
  which dereferences `e.Fields` and panics; fmt recovers and, because the receiver is a nil
  pointer, prints `<nil>`. Hence the log line `validation failed: <nil>`.
- In the handler, `errors.As(err, &verr)` succeeds (the chain contains a
  `*ValidationError`, just a nil one), but `len(verr.FieldErrors())` is 0 because
  `FieldErrors` is nil-safe, so the switch falls through to the 500 branch.
- Invalid flags still get 422 because `verr` is non-nil in that path. CI was green because
  the only PUT test posted an invalid flag.

Quick proof:

```go
err := validate(validFlag)
fmt.Printf("%T %v %v\n", err, err, err == nil)   // *flags.ValidationError <nil> false
```

## Red herring

The same commit added `omitempty` to `Description` and a DEBUG line "flag has no
description" right before each failure. The curl transcript shows the 500 also happens
with a description, and the 422 path shows JSON decoding is fine.

## Fix

```go
if verr == nil {
    return nil
}
return verr
```

Alternatives: have `validate` return `*ValidationError` and convert at the boundary
(`if v := validate(f); v != nil { return fmt.Errorf(...: %w, v) }`), or build a
`map[string]string` and only construct the error when the map is non-empty.

## Prevention

- Rule: never return a typed nil pointer through an interface; return a literal `nil`.
- Linters: `staticcheck` / `nilness` (go vet analyzer, via gopls or golangci-lint) and
  `nilnil`/`nilerr` catch many variants.
- A happy-path test for every write endpoint; mutation-test style review of refactors.
- Canary by replica or Argo Rollouts analysis on the PUT 5xx rate; this would have
  auto-aborted at 14:00.
