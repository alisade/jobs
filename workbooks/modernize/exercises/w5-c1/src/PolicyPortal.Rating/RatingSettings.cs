using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Configuration;
using System.Globalization;

namespace PolicyPortal.Rating
{
    /// <summary>Rating parameters. Values come from the host's App.config / Web.config appSettings.</summary>
    public sealed class RatingSettings
    {
        public decimal BaseRatePerThousand { get; private set; }
        public decimal MinimumPremium { get; private set; }
        public decimal ClaimSurchargePercent { get; private set; }
        public decimal SprinklerCreditPercent { get; private set; }
        public string QuoteCacheDir { get; private set; }
        public IReadOnlyDictionary<string, decimal> TerritoryFactors { get; private set; }

        /// <summary>The production settings.</summary>
        public static RatingSettings Load()
        {
            NameValueCollection app = ConfigurationManager.AppSettings;
            var values = new Dictionary<string, string>();
            foreach (string key in app.AllKeys)
            {
                values[key] = app[key];
            }
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
