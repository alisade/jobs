using System;

namespace PolicyPortal.Rating
{
    /// <summary>Annual premium for a commercial property risk (rating manual CP-2019, section 4).</summary>
    public sealed class PremiumCalculator
    {
        private readonly RatingSettings settings;

        public PremiumCalculator(RatingSettings settings)
        {
            this.settings = settings;
        }

        public decimal Annual(PolicyRisk risk)
        {
            decimal factor;
            if (!settings.TerritoryFactors.TryGetValue(risk.Territory, out factor))
            {
                throw new ArgumentException("unknown territory " + risk.Territory);
            }
            decimal premium = risk.InsuredValue / 1000m * settings.BaseRatePerThousand * factor;
            int claims = Math.Min(risk.ClaimsLast5Years, 3);
            premium *= 1m + claims * settings.ClaimSurchargePercent / 100m;
            if (risk.Sprinklered)
            {
                premium *= 1m - settings.SprinklerCreditPercent / 100m;
            }
            premium = Math.Round(premium, 2);
            return Math.Max(premium, settings.MinimumPremium);
        }
    }
}
