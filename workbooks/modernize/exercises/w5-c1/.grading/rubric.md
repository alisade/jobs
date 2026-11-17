# Rubric: modernize/w5-c1 PolicyPortal.Rating on .NET 10
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Correct replacements | 20 | Full: SDK-style net10.0 project with unused references dropped; settings shipped with the library (JSON content file, embedded resource, or IConfiguration with a named file) rather than relying on the host's config file; System.Text.Json cache with explicit naming options and safe handling of old entries; `IndexOf('\n')` or `StringComparison.Ordinal`. Partial: works through the System.Configuration.ConfigurationManager package with values copied into the test project's config (fragile: depends on the entry assembly). Zero: `EnableUnsafeBinaryFormatterSerialization`, or tests or fixtures edited. |
| 3 | Change log accuracy | 15 | Full: MSB3644 (no .NET Framework reference assemblies) and why SDK-style; ConfigurationManager reads the entry assembly's config (testhost under xunit, the batch exe in batch jobs); BinaryFormatter obsolete (SYSLIB0011) and throwing from .NET 9; .NET 5+ uses ICU on all platforms so culture-sensitive `IndexOf(string)` does not find "\n" inside "\r\n". Partial: generic "APIs changed". |
| 4 | Verification and rollout | 15 | Full: characterization tests before and after; a parallel run comparing premiums from the old and new builds on a sample of real quotes; cache entries left to expire or migrated once; a sweep of PolicyPortal for culture-sensitive string calls (CA1307/CA1309 analyzers); rollback named. Partial: one of these. |
Total: 100
