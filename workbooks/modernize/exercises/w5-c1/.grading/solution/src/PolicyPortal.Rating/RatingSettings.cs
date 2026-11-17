using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.Json;

namespace PolicyPortal.Rating
{
    /// <summary>
    /// Rating parameters. On .NET Framework these came from the host's App.config appSettings; on .NET the
    /// host's config file is not this library's (under a test runner it is testhost's), so the values ship
    /// with the library in rating.json, with the same keys.
    /// </summary>
    public sealed class RatingSettings
    {
        public decimal BaseRatePerThousand { get; private set; }
        public decimal MinimumPremium { get; private set; }
        public decimal ClaimSurchargePercent { get; private set; }
        public decimal SprinklerCreditPercent { get; private set; }
        public string QuoteCacheDir { get; private set; }
        public IReadOnlyDictionary<string, decimal> TerritoryFactors { get; private set; }

        /// <summary>The production settings, from rating.json next to the assembly (or an explicit path).</summary>
        public static RatingSettings Load(string path = null)
        {
            path = path ?? Path.Combine(AppContext.BaseDirectory, "rating.json");
            var values = JsonSerializer.Deserialize<Dictionary<string, string>>(File.ReadAllText(path));
            return FromValues(values);
        }

        /// <summary>Parse the Rating.* keys (same names as appSettings).</summary>
        public static RatingSettings FromValues(IReadOnlyDictionary<string, string> v)
        {
            var factors = new Dictionary<string, decimal>(StringComparer.OrdinalIgnoreCase);
            foreach (string pair in v["Rating.TerritoryFactors"].Split(';'))
            {
                string[] kv = pair.Split(':');
                factors[kv[0].Trim()] = decimal.Parse(kv[1], CultureInfo.InvariantCulture);
            }
            return new RatingSettings
            {
                BaseRatePerThousand = decimal.Parse(v["Rating.BaseRatePerThousand"], CultureInfo.InvariantCulture),
                MinimumPremium = decimal.Parse(v["Rating.MinimumPremium"], CultureInfo.InvariantCulture),
                ClaimSurchargePercent = decimal.Parse(v["Rating.ClaimSurchargePercent"], CultureInfo.InvariantCulture),
                SprinklerCreditPercent = decimal.Parse(v["Rating.SprinklerCreditPercent"], CultureInfo.InvariantCulture),
                QuoteCacheDir = v["Rating.QuoteCacheDir"],
                TerritoryFactors = factors,
            };
        }
    }
}
