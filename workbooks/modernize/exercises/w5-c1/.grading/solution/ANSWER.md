# ANSWER: modernize/w5-c1 PolicyPortal.Rating on .NET 10

## Approach

`make test` failed with MSB3644, so I converted the project first (by hand; Upgrade Assistant gives the same csproj),
then ran the characterization tests and fixed what the runtime showed, one change at a time.

## Fix

| Change | Breaking change behind it |
|---|---|
| SDK-style csproj, `net10.0`, `GenerateAssemblyInfo=false`, log4net and packages.config dropped | classic projects need .NET Framework reference assemblies (MSB3644 off Windows) |
| Settings moved from App.config to `rating.json` shipped with the library, same keys and values | `ConfigurationManager` reads the entry assembly's config: testhost under xunit, the exe in batch jobs |
| Quote cache: System.Text.Json, `<id>.json`, camelCase; `.bin` entries are misses | BinaryFormatter obsolete (SYSLIB0011), throws from .NET 9, unsafe on files |
| `IndexOf('\n')` and `IndexOf(':')` (ordinal) in the note parser | .NET 5+ uses ICU: culture-sensitive `IndexOf("\n")` returns -1 inside "\r\n" |

Premiums: unchanged, all characterization tests pass; decimal math and `Math.Round` are identical.

## Trade-offs / what I would do in production

Let old cache entries expire (30 days) rather than migrate them. In containers, move rating.json to a mounted config
or environment, with the same keys. Turn on CA1307/CA1309 across PolicyPortal to find the other culture-sensitive
string calls. Roll out with a parallel run comparing premiums from both builds on a week of real quotes; rollback is the
4.8 build behind the same interface.
