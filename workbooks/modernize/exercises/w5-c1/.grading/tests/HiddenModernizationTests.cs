using System.Reflection;
using System.Runtime.Versioning;
using System.Text.Json;
using Xunit;

namespace PolicyPortal.Rating.Tests;

public class HiddenModernizationTests
{
    private static string RepoRoot()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !Directory.Exists(Path.Combine(d.FullName, "src", "PolicyPortal.Rating")))
        {
            d = d.Parent;
        }
        Assert.NotNull(d);
        return d.FullName;
    }

    [Fact]
    public void LibraryTargetsModernDotNet()
    {
        var tfm = typeof(PremiumCalculator).Assembly.GetCustomAttribute<TargetFrameworkAttribute>();
        Assert.NotNull(tfm);
        Assert.StartsWith(".NETCoreApp,Version=v10", tfm.FrameworkName);
    }

    [Fact]
    public void ProjectIsSdkStyleWithoutPackagesConfig()
    {
        string proj = File.ReadAllText(Path.Combine(RepoRoot(), "src", "PolicyPortal.Rating", "PolicyPortal.Rating.csproj"));
        Assert.Contains("Sdk=\"Microsoft.NET.Sdk\"", proj);
        Assert.DoesNotContain("TargetFrameworkVersion", proj);
        Assert.DoesNotContain("packages.config\"", proj.Replace("Remove=\"packages.config\"", ""));
    }

    [Fact]
    public void NoBinaryFormatterLeft()
    {
        foreach (var f in Directory.GetFiles(Path.Combine(RepoRoot(), "src"), "*.cs", SearchOption.AllDirectories))
        {
            Assert.DoesNotContain("BinaryFormatter", File.ReadAllText(f));
        }
    }

    [Fact]
    public void ProductionSettingsStillLoad()
    {
        var s = RatingSettings.Load();
        Assert.Equal(4.25m, s.BaseRatePerThousand);
        Assert.Equal(350.00m, s.MinimumPremium);
        Assert.Equal(10m, s.ClaimSurchargePercent);
        Assert.Equal(7.5m, s.SprinklerCreditPercent);
        Assert.Equal(1.58m, s.TerritoryFactors["D"]);
        Assert.Equal(1.15m, s.TerritoryFactors["b"]);
        Assert.False(string.IsNullOrWhiteSpace(s.QuoteCacheDir));
    }

    [Theory]
    [InlineData("A", 99000, 0, false, "420.75")]
    [InlineData("C", 1000000, 3, true, "6746.02")]
    [InlineData("D", 3333333, 1, false, "24621.66")]
    [InlineData("B", 60000, 0, true, "350.00")]
    public void LoadedSettingsGiveProductionPremiums(string t, int value, int claims, bool spr, string expected)
    {
        var calc = new PremiumCalculator(RatingSettings.Load());
        var risk = new PolicyRisk { Territory = t, InsuredValue = value, ClaimsLast5Years = claims, Sprinklered = spr };
        Assert.Equal(decimal.Parse(expected, System.Globalization.CultureInfo.InvariantCulture), calc.Annual(risk));
    }

    [Fact]
    public void NotesWithWindowsLineEndings()
    {
        var tags = PolicyNoteParser.Parse("UW: approved\r\nREF: inspection due 2027-01\r\nLOSS: none in 5 years");
        Assert.Equal("approved", tags["UW"]);
        Assert.Equal("inspection due 2027-01", tags["REF"]);
        Assert.Equal("none in 5 years", tags["LOSS"]);
    }

    [Fact]
    public void NotesWithMixedEndingsAndTrailingNewline()
    {
        var tags = PolicyNoteParser.Parse("free text first\r\nUW: declined\nREF: see file\r\n");
        Assert.Equal(2, tags.Count);
        Assert.Equal("declined", tags["UW"]);
        Assert.Equal("see file", tags["REF"]);
    }

    [Fact]
    public void QuoteCacheReadsTheAgreedJsonFormat()
    {
        string dir = Directory.CreateTempSubdirectory("qc").FullName;
        File.Copy(Path.Combine(AppContext.BaseDirectory, "fixtures", "quote-cache", "Q-2026-000731.json"), Path.Combine(dir, "Q-2026-000731.json"));
        var q = new QuoteCache(dir).TryLoad("Q-2026-000731");
        Assert.NotNull(q);
        Assert.Equal("CP-7740213", q.PolicyNumber);
        Assert.Equal("C", q.Territory);
        Assert.Equal(20055.75m, q.Premium);
        Assert.Equal(new DateTime(2026, 11, 12, 14, 3, 22, DateTimeKind.Utc), q.CreatedUtc.ToUniversalTime());
    }

    [Fact]
    public void QuoteCacheRoundTripsAndWritesCamelCaseJson()
    {
        string dir = Directory.CreateTempSubdirectory("qc").FullName;
        var cache = new QuoteCache(dir);
        var created = new DateTime(2026, 11, 13, 9, 30, 0, DateTimeKind.Utc);
        cache.Save(new Quote { QuoteId = "Q-2026-000900", PolicyNumber = "CP-1", Territory = "A", Premium = 5312.50m, CreatedUtc = created });
        var back = cache.TryLoad("Q-2026-000900");
        Assert.Equal(5312.50m, back.Premium);
        Assert.Equal(created, back.CreatedUtc.ToUniversalTime());
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, "Q-2026-000900.json")));
        Assert.Equal("CP-1", doc.RootElement.GetProperty("policyNumber").GetString());
        Assert.Equal(5312.50m, doc.RootElement.GetProperty("premium").GetDecimal());
    }

    [Fact]
    public void LegacyBinaryEntriesAreCacheMisses()
    {
        string dir = Directory.CreateTempSubdirectory("qc").FullName;
        File.WriteAllBytes(Path.Combine(dir, "Q-2019-000001.bin"), new byte[] { 0, 1, 0, 0, 0, 255, 255, 255, 255 });
        var cache = new QuoteCache(dir);
        Assert.Null(cache.TryLoad("Q-2019-000001"));
        Assert.Null(cache.TryLoad("Q-does-not-exist"));
    }
}
