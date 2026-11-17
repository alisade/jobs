namespace PolicyPortal.Rating.Tests;

/// <summary>The production values from App.config, as a dictionary, so tests do not depend on config loading.</summary>
internal static class Production
{
    public static readonly IReadOnlyDictionary<string, string> Values = new Dictionary<string, string>
    {
        ["Rating.BaseRatePerThousand"] = "4.25",
        ["Rating.MinimumPremium"] = "350.00",
        ["Rating.TerritoryFactors"] = "A:1.00;B:1.15;C:1.32;D:1.58",
        ["Rating.ClaimSurchargePercent"] = "10",
        ["Rating.SprinklerCreditPercent"] = "7.5",
        ["Rating.QuoteCacheDir"] = "C:\\PolicyPortal\\QuoteCache",
    };

    public static PremiumCalculator Calculator() => new PremiumCalculator(RatingSettings.FromValues(Values));
}
