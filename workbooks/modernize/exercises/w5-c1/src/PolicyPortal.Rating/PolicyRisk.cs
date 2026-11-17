namespace PolicyPortal.Rating
{
    /// <summary>The rating inputs for one commercial property risk.</summary>
    public sealed class PolicyRisk
    {
        public string Territory { get; set; }
        public decimal InsuredValue { get; set; }
        public int ClaimsLast5Years { get; set; }
        public bool Sprinklered { get; set; }
    }
}
