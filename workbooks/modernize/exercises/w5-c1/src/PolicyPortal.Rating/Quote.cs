using System;

namespace PolicyPortal.Rating
{
    [Serializable]
    public sealed class Quote
    {
        public string QuoteId { get; set; }
        public string PolicyNumber { get; set; }
        public string Territory { get; set; }
        public decimal Premium { get; set; }
        public DateTime CreatedUtc { get; set; }
    }
}
