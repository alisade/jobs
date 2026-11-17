using Xunit;

namespace PolicyPortal.Rating.Tests;

/// <summary>Premiums captured from production on .NET Framework 4.8 (portal release 3.8.0). They must not change.</summary>
public class CharacterizationTests
{
    [Theory]
    [InlineData("A", 1250000, 0, false, "5312.50")]
    [InlineData("B", 480000, 1, true, "2387.06")]
    [InlineData("C", 2750000, 4, false, "20055.75")]
    [InlineData("D", 50000, 0, true, "350.00")]
    [InlineData("b", 333333, 2, true, "1808.37")]
    public void PremiumUnchanged(string territory, int insuredValue, int claims, bool sprinklered, string expected)
    {
        var risk = new PolicyRisk { Territory = territory, InsuredValue = insuredValue, ClaimsLast5Years = claims, Sprinklered = sprinklered };
        Assert.Equal(decimal.Parse(expected, System.Globalization.CultureInfo.InvariantCulture), Production.Calculator().Annual(risk));
    }

    [Fact]
    public void NotesWithUnixLineEndings()
    {
        var tags = PolicyNoteParser.Parse("UW: approved with sprinkler credit\nREF: inspection due 2027-01\nfree text line");
        Assert.Equal("approved with sprinkler credit", tags["UW"]);
        Assert.Equal("inspection due 2027-01", tags["REF"]);
    }
}
