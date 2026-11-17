# Reference: modernize/w5-c1

Files: `.grading/solution/src/PolicyPortal.Rating/` (csproj, rating.json, RatingSettings.cs, QuoteCache.cs,
PolicyNoteParser.cs, Quote.cs).

1. Project: the classic csproj needs the .NET Framework 4.8 reference assemblies (MSB3644 off Windows). SDK-style
   `net10.0`, `GenerateAssemblyInfo=false` to keep `Properties/AssemblyInfo.cs`, log4net reference dropped (unused).
2. Settings: `ConfigurationManager.AppSettings` reads the entry assembly's config file. On .NET Framework that was the
   portal's Web.config; on .NET under xunit it is testhost's, so every key is missing. The values move to
   `rating.json`, shipped as content next to the library; `Load(path = null)` reads it. Same keys, same values.
3. Cache: BinaryFormatter is obsolete (SYSLIB0011) and its methods throw from .NET 9. System.Text.Json with camelCase,
   `<id>.json`; `.bin` files are simply not read (cache misses, expire within 30 days).
4. Notes: .NET 5+ uses ICU on every OS; `string.IndexOf(string)` is culture-sensitive and "\r\n" is treated as one
   unit, so `IndexOf("\n")` returns -1 on CRLF text. `IndexOf('\n')` (char overloads are ordinal) fixes it.
5. `PremiumCalculator` is unchanged: decimal arithmetic and `Math.Round(decimal, 2)` (banker's rounding) behave the same.

Talking points: what Upgrade Assistant converts (project file, packages) vs what it cannot see (runtime behaviour);
CA1307/CA1309/CA1310 analyzers for the string-comparison sweep; why characterization tests decide equivalence.
