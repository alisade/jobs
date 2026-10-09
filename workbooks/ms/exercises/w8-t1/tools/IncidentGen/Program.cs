using System.Globalization;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using Dataverse.Sim;
using Fabrikam.Plugins;
using Microsoft.Xrm.Sdk;

// Replays Thursday's order submissions against the CURRENT code + registration/steps.json and writes
// what Finance and the platform recorded into ./incident.
var outDir = args.Length > 0 ? args[0] : "incident";
var root = FindRoot();
Directory.CreateDirectory(outDir);
var inv = CultureInfo.InvariantCulture;

var reg = RegistrationFile.Load(Path.Combine(root, "registration", "steps.json"));
var p = new Pipeline(typeof(CreditCheckPlugin).Assembly, reg.Steps)
{
    OrganizationName = "fabrikam-prod",
    DefaultCostMs = 40,
    Clock = new DateTime(2026, 10, 2, 9, 15, 0, DateTimeKind.Utc),
};
var customers = new Dictionary<Guid, string>
{
    [Guid.Parse("0a6f3c1e-2b4d-4e8f-9a1c-3d5e7f9b1c2d")] = "Contoso Hospitality",
    [Guid.Parse("1b7e4d2f-3c5e-4f9a-8b2d-4e6f8a0c2d3e")] = "Northwind Traders",
    [Guid.Parse("2c8f5e3a-4d6f-4a0b-9c3e-5f7a9b1d3e4f")] = "Litware Inc",
    [Guid.Parse("3d9a6f4b-5e7a-4b1c-8d4f-6a8b0c2e4f5a")] = "Adventure Works",
};
var limits = new Dictionary<string, (decimal Limit, decimal Open)>
{
    ["Contoso Hospitality"] = (50_000m, 20_000m), ["Northwind Traders"] = (30_000m, 5_000m),
    ["Litware Inc"] = (40_000m, 12_500m), ["Adventure Works"] = (15_000m, 2_000m),
};
foreach (var (id, name) in customers)
{
    var a = new Entity(Account.EntityName, id);
    a[Account.Name] = name; a[Account.CreditLimit] = new Money(limits[name].Limit); a[Account.OpenBalance] = new Money(limits[name].Open);
    p.Seed(a);
}
Guid C(string name) => customers.First(kv => kv.Value == name).Key;

var submissions = new (string No, string Customer, decimal Amount, bool Expired, string Rep)[]
{
    ("SO-58001", "Contoso Hospitality", 12_400m, false, "jamal.reed"),
    ("SO-58002", "Northwind Traders", 8_900m, true, "ana.silva"),
    ("SO-58003", "Litware Inc", 52_000m, false, "jamal.reed"),
    ("SO-58004", "Northwind Traders", 8_900m, false, "ana.silva"),
    ("SO-58005", "Adventure Works", 3_150m, true, "kim.yu"),
    ("SO-58006", "Adventure Works", 3_150m, false, "kim.yu"),
    ("SO-58007", "Contoso Hospitality", 4_780m, false, "kim.yu"),
};

var seen = new StringBuilder();
seen.AppendLine("# What sales reps saw in the Fabrikam Sales app, 2026-10-02 (UTC)");
seen.AppendLine();
var numbers = new Dictionary<Guid, string>();
foreach (var s in submissions)
{
    p.Advance(14 * 60_000);
    var o = new Entity(Order.EntityName);
    o[Order.Number] = s.No;
    o[Order.Customer] = new EntityReference(Account.EntityName, C(s.Customer));
    o[Order.Amount] = new Money(s.Amount);
    o[Order.PriceList] = s.Expired ? "FAB-2026Q3" : "FAB-2026Q4";
    o[Order.PriceListExpiresOn] = s.Expired ? new DateTime(2026, 9, 30, 23, 59, 59, DateTimeKind.Utc) : new DateTime(2026, 12, 31, 23, 59, 59, DateTimeKind.Utc);
    var at = p.Clock;
    try
    {
        var id = p.ClientService().Create(o);
        numbers[id] = s.No;
        seen.AppendLine($"- {at:HH:mm} {s.Rep} submitted {s.No} for {s.Customer}, {s.Amount.ToString("0.00", inv)}: order created");
    }
    catch (Exception ex)
    {
        seen.AppendLine($"- {at:HH:mm} {s.Rep} submitted {s.No} for {s.Customer}, {s.Amount.ToString("0.00", inv)}: Business Process Error: {ex.Message}");
    }
}

string Csv(string? v) => v == null ? "" : (v.Contains(',') || v.Contains('"') ? "\"" + v.Replace("\"", "\"\"") + "\"" : v);
string Money2(Entity e, string col) => (e.GetAttributeValue<Money>(col)?.Value ?? 0m).ToString("0.00", inv);

var orders = new StringBuilder("contoso_orderid,contoso_name,customer,contoso_amount,contoso_pricelistcode,createdon\n");
foreach (var o in p.All(Order.EntityName).OrderBy(o => o.GetAttributeValue<string>(Order.Number)))
    orders.AppendLine(string.Join(",", o.Id, o.GetAttributeValue<string>(Order.Number), Csv(customers[o.GetAttributeValue<EntityReference>(Order.Customer).Id]),
        Money2(o, Order.Amount), o.GetAttributeValue<string>(Order.PriceList), "2026-10-02"));
File.WriteAllText(Path.Combine(outDir, "orders-export.csv"), orders.ToString());

var audits = new StringBuilder("contoso_creditauditid,contoso_name,contoso_ordernumber,contoso_orderid,customer,contoso_amount,contoso_availablecredit,contoso_decision,contoso_checkedon\n");
foreach (var a in p.All(CreditAudit.EntityName).OrderBy(a => a.GetAttributeValue<DateTime>(CreditAudit.CheckedOn)))
    audits.AppendLine(string.Join(",", a.Id, Csv(a.GetAttributeValue<string>(CreditAudit.Name)), a.GetAttributeValue<string>(CreditAudit.OrderNumber),
        a.GetAttributeValue<EntityReference>(CreditAudit.OrderId)?.Id.ToString() ?? "",
        Csv(customers[a.GetAttributeValue<EntityReference>(CreditAudit.Customer).Id]), Money2(a, CreditAudit.Amount), Money2(a, CreditAudit.Available),
        a.GetAttributeValue<string>(CreditAudit.Decision), a.GetAttributeValue<DateTime>(CreditAudit.CheckedOn).ToString("o")));
File.WriteAllText(Path.Combine(outDir, "creditaudit-export.csv"), audits.ToString());

var approvedTotal = p.All(CreditAudit.EntityName).Where(a => a.GetAttributeValue<string>(CreditAudit.Decision) == "Approved").Sum(a => a.GetAttributeValue<Money>(CreditAudit.Amount).Value);
var ordersTotal = p.All(Order.EntityName).Sum(o => o.GetAttributeValue<Money>(Order.Amount).Value);
File.WriteAllText(Path.Combine(outDir, "finance-ticket.md"),
    "# FIN-2291 Credit exposure ledger does not reconcile (opened 2026-10-03 08:10 by Priya Nair, Finance Ops)\n\n" +
    "Every morning we reconcile contoso_creditaudit (the credit-exposure ledger, one row per order) against\n" +
    "contoso_order. Since the 2.7 release the ledger is higher than the order book, and it contains order\n" +
    "numbers that sales say were never created. Our exposure report to the bank covenant is overstated.\n\n" +
    $"- Approved ledger total for 2026-10-02: {approvedTotal.ToString("0.00", inv)}\n" +
    $"- Order book total for 2026-10-02: {ordersTotal.ToString("0.00", inv)}\n" +
    $"- Ledger rows: {p.All(CreditAudit.EntityName).Count}, orders: {p.All(Order.EntityName).Count}\n\n" +
    "Exports attached: orders-export.csv, creditaudit-export.csv. Please fix and tell us which rows to void.\n");
File.WriteAllText(Path.Combine(outDir, "sales-app.md"), seen.ToString());

// Red herring: last month's synchronous shipping-quote timeouts, fixed under INC-4471.
var herring = new List<TraceRecord>();
foreach (var (min, order) in new[] { (3, "SO-57112"), (11, "SO-57118"), (26, "SO-57131") })
{
    var st = new DateTime(2026, 9, 12, 15, min, 4, DateTimeKind.Utc);
    herring.Add(new TraceRecord
    {
        TypeName = "Fabrikam.Plugins.ShippingQuotePlugin", MessageName = "Create", PrimaryEntity = Order.EntityName, Depth = 1, Mode = 0, Stage = 40,
        CorrelationId = Guid.NewGuid(), RequestId = Guid.NewGuid(), PerformanceExecutionStartTime = st, CreatedOn = st.AddMilliseconds(120_011),
        PerformanceExecutionDuration = 120_011,
        MessageBlock = $"ShippingQuotePlugin: Mode=0 Depth=1 Order={order} POST https://quotes.carrier.example/v1/freight (timeout 100 s)",
        ExceptionDetails = "Exception type: System.ServiceModel.FaultException`1[Microsoft.Xrm.Sdk.OrganizationServiceFault]\nMessage: The plug-in execution failed because the operation has timed-out at the Sandbox Host.\nErrorCode: -2147204750 (0x80044172)",
    });
}
var json = new JsonSerializerOptions { WriteIndented = true, Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
var rows = herring.Concat(p.Traces).OrderBy(t => t.PerformanceExecutionStartTime).Select(t => new Dictionary<string, object?>
{
    ["typename"] = t.TypeName, ["messagename"] = t.MessageName, ["primaryentity"] = t.PrimaryEntity, ["depth"] = t.Depth,
    ["mode"] = t.Mode, ["correlationid"] = t.CorrelationId, ["createdon"] = t.CreatedOn.ToString("o"),
    ["performanceexecutionstarttime"] = t.PerformanceExecutionStartTime.ToString("o"),
    ["performanceexecutionduration"] = t.PerformanceExecutionDuration, ["messageblock"] = t.MessageBlock, ["exceptiondetails"] = t.ExceptionDetails,
}).ToList();
File.WriteAllText(Path.Combine(outDir, "plugintracelog.json"), JsonSerializer.Serialize(new Dictionary<string, object> { ["value"] = rows }, json) + "\n");

File.WriteAllText(Path.Combine(outDir, "INC-4471.md"),
    "# INC-4471 Order save takes 2 minutes then fails (RESOLVED 2026-09-15)\n\n" +
    "Cause: ShippingQuotePlugin was a synchronous PostOperation step calling the carrier API with a 100 s\n" +
    "HTTP timeout; during the carrier's slowdown on 2026-09-12 saves hit the 2-minute limit and failed with\n" +
    "0x80044172 (timed-out at the Sandbox Host).\n\n" +
    "Fix (release 2.6.3, 2026-09-15): step changed to Asynchronous PostOperation, HTTP timeout 10 s, quote\n" +
    "written back by the async job. No recurrence since. Closed by: R. Mbeki.\n");
File.Copy(Path.Combine(root, "registration", "steps.json"), Path.Combine(outDir, "steps-export.json"), true);
Console.WriteLine($"incident bundle written to {Path.GetFullPath(outDir)}");

static string FindRoot()
{
    var dir = new DirectoryInfo(Directory.GetCurrentDirectory());
    while (dir != null && !Directory.Exists(Path.Combine(dir.FullName, "registration"))) dir = dir.Parent;
    return dir?.FullName ?? throw new InvalidOperationException("run from the exercise folder");
}
