namespace Tailspin.Plugins
{
    /// <summary>Schema names for contoso_workorder (provided).</summary>
    public static class WorkOrder
    {
        public const string EntityName = "contoso_workorder";
        public const string PrimaryKey = "contoso_workorderid";
        public const string Number = "contoso_name";
        public const string Description = "contoso_description";
        public const string LaborHours = "contoso_laborhours";          // Decimal
        public const string LaborRate = "contoso_laborrate";            // Currency (Money)
        public const string PartsCost = "contoso_partscost";            // Currency (Money)
        public const string TotalCost = "contoso_totalcost";            // Currency (Money), derived
        public const string LastCalculatedOn = "contoso_lastcalculatedon"; // Date and time (UTC), derived
        public const string PartsList = "contoso_partslist";            // Multiline text (JSON)
    }
}
