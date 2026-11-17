# modernize/w5-c1 - PolicyPortal.Rating: .NET Framework 4.8 to .NET 10

**Type:** coding | **Estimate:** 2.5 hours | **Study plan:** Week 5 (Mon: porting guide and project format; Tue: what breaks; Wed: Upgrade Assistant and agent-assisted upgrades)

## Scenario

Corvane Mutual's agent portal (PolicyPortal) is an ASP.NET MVC 5 application on .NET Framework
4.8 and Windows Server 2016. The plan (CLM-4520) is to move it to .NET 10 on Linux containers,
one library at a time, starting with `PolicyPortal.Rating`: the commercial property rating code
the portal and two batch jobs share. The underwriting team has one condition: the premiums do not
change by a cent. Last year someone added an SDK-style xunit project with characterization tests
captured from production; that is your safety net.

On this machine the library does not even build: it is a classic project that targets .NET
Framework 4.8.

## What you have

| Path | What it is |
|---|---|
| `src/PolicyPortal.Rating/` | classic csproj, `packages.config`, `App.config` with the production rating parameters, the code |
| `tests/PolicyPortal.Rating.Tests/` | SDK-style xunit project (net10.0) with characterization tests |
| `fixtures/quote-cache/` | a quote cache entry in the format agreed with the Java rating service |
| `Directory.Build.props` | shared build settings |

## Requirements

1. Convert the library to an SDK-style project targeting `net10.0` (no `packages.config`, no
   `TargetFrameworkVersion`). Drop references nothing uses.
2. Settings: `RatingSettings.Load()` must return the production values that are in `App.config`
   today, when the library runs under any host (the portal, a batch job, or the test runner).
   Keep `RatingSettings.FromValues(...)` and the key names.
3. Quote cache: replace the binary serializer with System.Text.Json. Files are
   `<quoteId>.json`, camelCase properties, the format in `fixtures/quote-cache/`. Old entries from
   the .NET Framework cache must not crash the portal: treat them as cache misses.
4. Note parsing: `PolicyNoteParser.Parse` must give the same tags for notes with Windows (`\r\n`)
   and Unix (`\n`) line endings. Notes stored by the portal use `\r\n`.
5. Premiums for the same inputs stay identical (`PremiumCalculator` is not the problem; prove it).
6. `ANSWER.md`: a change log with the breaking change behind each fix.

## Acceptance criteria (what the grader checks)

- The library builds for .NET 10 as an SDK-style project; no `BinaryFormatter` remains.
- Hidden tests: `RatingSettings.Load()` returns the production values; premiums computed from the
  loaded settings match production; notes parse correctly with `\r\n` and mixed endings; the quote
  cache reads the agreed fixture, round-trips, writes camelCase JSON, and treats old `.bin`
  entries as misses.
- `ANSWER.md` explains each breakage (project system, configuration, BinaryFormatter, ICU string
  comparison) and the rollout.

## How to run

```bash
make setup      # checks the .NET SDK, restores NuGet packages once
make test       # visible characterization tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/w5-c1
make clean
```

Tip: the .NET Upgrade Assistant and agent-based upgrade tools do the project conversion well.
Run one if you like; then check the behaviour changes they do not touch.
