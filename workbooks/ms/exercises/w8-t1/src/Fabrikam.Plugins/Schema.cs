namespace Fabrikam.Plugins
{
    /// <summary>Schema names (provided).</summary>
    public static class Account
    {
        public const string EntityName = "account";
        public const string Name = "name";
        public const string CreditLimit = "contoso_creditlimit";   // Money
        public const string OpenBalance = "contoso_openbalance";   // Money
    }

    public static class Order
    {
        public const string EntityName = "contoso_order";
        public const string Number = "contoso_name";
        public const string Customer = "contoso_customerid";              // Lookup to account
        public const string Amount = "contoso_amount";                    // Money
        public const string PriceList = "contoso_pricelistcode";          // Text
        public const string PriceListExpiresOn = "contoso_pricelistexpireson"; // Date and time (UTC)
    }

    /// <summary>Finance's credit-exposure ledger: one row per created order.</summary>
    public static class CreditAudit
    {
        public const string EntityName = "contoso_creditaudit";
        public const string Name = "contoso_name";
        public const string OrderNumber = "contoso_ordernumber";  // Text
        public const string OrderId = "contoso_orderid";          // Lookup to contoso_order
        public const string Customer = "contoso_customerid";      // Lookup to account
        public const string Amount = "contoso_amount";            // Money
        public const string Available = "contoso_availablecredit"; // Money
        public const string Decision = "contoso_decision";        // Text: Approved | Declined
        public const string CheckedOn = "contoso_checkedon";      // Date and time (UTC)
    }
}
