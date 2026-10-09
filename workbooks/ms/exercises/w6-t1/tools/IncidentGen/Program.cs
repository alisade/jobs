using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using Dataverse.Sim;
using Microsoft.Xrm.Sdk;
using Tailspin.Plugins;

// Replays the saves dispatchers made on 2026-10-08 against the CURRENT plug-in code and
// registration/steps.json, and writes what the platform would have recorded into ./incident.
var outDir = args.Length > 0 ? args[0] : "incident";
var root = FindRoot();
Directory.CreateDirectory(outDir);

var reg = RegistrationFile.Load(Path.Combine(root, "registration", "steps.json"));
var p = new Pipeline(typeof(WorkOrderRollupPlugin).Assembly, reg.Steps)
{
    OrganizationName = "tailspin-prod",
    DefaultCostMs = 400,
    Clock = new DateTime(2026, 10, 8, 14, 2, 11, DateTimeKind.Utc),
};

var orders = new[]
{
    (Id: Guid.Parse("3d6c1f0e-8a52-4b7e-9f13-0c4a5e2d7b61"), No: "WO-10421", Desc: "Walk-in freezer not holding temperature", H: 2m, R: 95m, P: 140m),
    (Id: Guid.Parse("b7a2e914-5c1d-4f08-a3e6-9d0f2c7b4e15"), No: "WO-10388", Desc: "Ice machine leaking - replace inlet valve", H: 1m, R: 95m, P: 62.5m),
    (Id: Guid.Parse("e40c9d27-1b6f-4a83-8e52-7f3d0a9c6b28"), No: "WO-10440", Desc: "Rooftop unit compressor noise", H: 4m, R: 120m, P: 0m),
};
foreach (var o in orders)
{
    var e = new Entity(WorkOrder.EntityName, o.Id);
    e[WorkOrder.Number] = o.No; e[WorkOrder.Description] = o.Desc;
    e[WorkOrder.LaborHours] = o.H; e[WorkOrder.LaborRate] = new Money(o.R); e[WorkOrder.PartsCost] = new Money(o.P);
    p.Seed(e);
}

var saves = new List<(string Who, Guid Id, string No, (string, object)[] Changes, string What)>
{
    ("maria.okafor@tailspin.example", orders[0].Id, orders[0].No, new (string, object)[] { (WorkOrder.LaborHours, 3.5m) }, "labor hours 2 -> 3.5"),
    ("maria.okafor@tailspin.example", orders[0].Id, orders[0].No, new (string, object)[] { (WorkOrder.LaborHours, 3.5m) }, "retry"),
    ("dev.patel@tailspin.example", orders[1].Id, orders[1].No, new (string, object)[] { (WorkOrder.Description, "Ice machine leaking - replace inlet valve (unit 2)") }, "description typo fix"),
    ("li.wong@tailspin.example", orders[2].Id, orders[2].No, new (string, object)[] { (WorkOrder.PartsCost, new Money(310m)) }, "parts cost 0 -> 310"),
};

var client = new StringBuilder();
client.AppendLine("# What the callers saw (model-driven app 'Dispatch Hub' and the parts-sync integration), 2026-10-08 UTC");
client.AppendLine();
var errors = new List<object>();
foreach (var s in saves)
{
    p.Advance(37_000);
    var startedAt = p.Clock;
    var corr = Guid.NewGuid();
    var e = new Entity(WorkOrder.EntityName, s.Id);
    foreach (var (n, v) in s.Changes) e[n] = v;
    try
    {
        p.ClientService(corr).Update(e);
        client.AppendLine($"- {startedAt:HH:mm:ss} {s.Who} saved {s.No} ({s.What}): saved OK after {(p.Clock - startedAt).TotalMilliseconds:0} ms server time");
    }
    catch (DataverseFault f)
    {
        var ms = (p.Clock - startedAt).TotalMilliseconds;
        client.AppendLine($"- {startedAt:HH:mm:ss} {s.Who} saved {s.No} ({s.What}): spinner, then 'Business Process Error' dialog after {ms:0} ms server time (+ network/UI). Row not saved.");
        var lastTrace = p.Traces.Where(t => t.CorrelationId == corr && t.ExceptionDetails != null).OrderByDescending(t => t.Depth).FirstOrDefault();
        errors.Add(new Dictionary<string, object?>
        {
            ["when"] = startedAt.ToString("o"),
            ["request"] = $"PATCH [org]/api/data/v9.2/contoso_workorders({s.Id})",
            ["error"] = new Dictionary<string, object?>
            {
                ["code"] = f.HexCode,
                ["message"] = f.Message,
                ["@Microsoft.PowerApps.CDS.ErrorDetails.ApiExceptionSourceKey"] = "Plugin/" + (lastTrace?.TypeName ?? "unknown"),
                ["@Microsoft.PowerApps.CDS.ErrorDetails.ApiDepthKey"] = (lastTrace?.Depth ?? 0).ToString(),
                ["@Microsoft.PowerApps.CDS.ErrorDetails.ApiExceptionHttpStatusCode"] = "400",
                ["@Microsoft.PowerApps.CDS.ErrorDetails.ApiActivityIdKey"] = corr.ToString(),
            },
        });
    }
}

// Red herring: async vendor-call timeouts on Monday during the Northwind Parts API outage.
var herring = new List<TraceRecord>();
var t0 = new DateTime(2026, 10, 6, 13, 7, 42, DateTimeKind.Utc);
for (var i = 0; i < 4; i++)
{
    var start = t0.AddMinutes(i * 9 + (i % 2) * 2);
    herring.Add(new TraceRecord
    {
        TypeName = "Tailspin.Plugins.PartsAvailabilityPlugin", MessageName = "Update", PrimaryEntity = WorkOrder.EntityName,
        Depth = 1, Mode = 1, Stage = 40, CorrelationId = Guid.NewGuid(), RequestId = Guid.NewGuid(),
        PerformanceExecutionStartTime = start, CreatedOn = start.AddMilliseconds(120_004), PerformanceExecutionDuration = 120_004,
        MessageBlock = $"PartsAvailabilityPlugin: Depth=1 Id={orders[i % 3].Id} calling https://api.northwindparts.example/v2/availability",
        ExceptionDetails = "Exception type: System.ServiceModel.FaultException`1[Microsoft.Xrm.Sdk.OrganizationServiceFault]\nMessage: The plug-in execution failed because the operation has timed-out at the Sandbox Host.\nErrorCode: -2147204750 (0x80044172)",
    });
}

var all = herring.Concat(p.Traces).OrderBy(t => t.CreatedOn).ToList();
var json = new JsonSerializerOptions { WriteIndented = true, Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
var rows = all.Select(t => new Dictionary<string, object?>
{
    ["plugintracelogid"] = Guid.NewGuid(),
    ["typename"] = t.TypeName,
    ["messagename"] = t.MessageName,
    ["primaryentity"] = t.PrimaryEntity,
    ["depth"] = t.Depth,
    ["mode"] = t.Mode,
    ["operationtype"] = t.OperationType,
    ["correlationid"] = t.CorrelationId,
    ["requestid"] = t.RequestId,
    ["createdon"] = t.CreatedOn.ToString("o"),
    ["performanceexecutionstarttime"] = t.PerformanceExecutionStartTime.ToString("o"),
    ["performanceexecutionduration"] = t.PerformanceExecutionDuration,
    ["messageblock"] = t.MessageBlock,
    ["exceptiondetails"] = t.ExceptionDetails,
}).ToList();
File.WriteAllText(Path.Combine(outDir, "plugintracelog.json"),
    JsonSerializer.Serialize(new Dictionary<string, object> { ["@odata.context"] = "https://tailspin-prod.crm.dynamics.com/api/data/v9.2/$metadata#plugintracelogs", ["value"] = rows }, json) + "\n");
File.WriteAllText(Path.Combine(outDir, "client-errors.json"), JsonSerializer.Serialize(errors, json) + "\n");
File.WriteAllText(Path.Combine(outDir, "user-reports.md"), client.ToString());

// Ops view, computed from the trace rows above.
var saveCount = saves.Count;
var rollupRuns = p.Traces.Count(t => t.TypeName.EndsWith("WorkOrderRollupPlugin"));
var retrieves = p.Calls.Count(c => c.Message == "Retrieve");
var updates = p.Calls.Count(c => c.Message == "Update");
var ops = new StringBuilder();
ops.AppendLine("# Ops alert digest - tailspin-prod (Dataverse), 2026-10-08");
ops.AppendLine();
ops.AppendLine("PagerDuty: [P2] Dispatch Hub save failures + Dataverse plug-in CPU above baseline (fired 14:05 UTC)");
ops.AppendLine();
ops.AppendLine("Power Platform admin center > Analytics > Dataverse > Plug-ins (sample window, replayed):");
ops.AppendLine();
ops.AppendLine("| metric | value |");
ops.AppendLine("|---|---|");
ops.AppendLine($"| user save requests (PATCH contoso_workorders) | {saveCount} |");
ops.AppendLine($"| plug-in executions, Tailspin.Plugins.WorkOrderRollupPlugin | {rollupRuns} |");
ops.AppendLine($"| Update requests reaching the pipeline | {updates} |");
ops.AppendLine($"| Retrieve requests | {retrieves} |");
ops.AppendLine($"| failed saves | {errors.Count} |");
ops.AppendLine();
ops.AppendLine("Dataverse API request volume for the app user and dispatchers is up roughly an order of magnitude");
ops.AppendLine("since the morning of 2026-10-07. Sandbox CPU per org at 3x the 30-day p95. No platform incident");
ops.AppendLine("is posted for the region in the Power Platform admin center Service health page.");
File.WriteAllText(Path.Combine(outDir, "ops-alert.md"), ops.ToString());

File.WriteAllText(Path.Combine(outDir, "vendor-status.md"),
    "# status.northwindparts.example - incident history\n\n" +
    "## 2026-10-06 - Availability API degraded (RESOLVED)\n\n" +
    "- 12:58 UTC Investigating: elevated latency and timeouts on /v2/availability.\n" +
    "- 13:21 UTC Identified: a failed database failover in us-central.\n" +
    "- 13:44 UTC Resolved: latency back to normal (p95 180 ms). No further impact expected.\n\n" +
    "No incidents reported 2026-10-07 to 2026-10-08.\n");

File.WriteAllText(Path.Combine(outDir, "release-notes.md"),
    "# Tailspin Dispatch solution - release notes\n\n" +
    "## 3.4.0 (imported to PROD 2026-10-07 07:40 UTC, managed)\n\n" +
    "- NEW: WorkOrderRollupPlugin keeps Total Cost and Last Calculated On up to date on every save\n" +
    "  (finance asked for totals to be correct without the nightly flow).\n" +
    "- Removed the nightly 'Recalculate work order totals' cloud flow.\n" +
    "- Form: Total Cost is read-only.\n\n" +
    "## 3.3.2 (2026-09-29)\n\n" +
    "- PartsAvailabilityPlugin endpoint moved to unsecure configuration.\n");

File.Copy(Path.Combine(root, "registration", "steps.json"), Path.Combine(outDir, "steps-export.json"), true);
Console.WriteLine($"incident bundle written to {Path.GetFullPath(outDir)} ({rows.Count} trace rows, {errors.Count} failed saves)");

static string FindRoot()
{
    var dir = new DirectoryInfo(Directory.GetCurrentDirectory());
    while (dir != null && !Directory.Exists(Path.Combine(dir.FullName, "registration"))) dir = dir.Parent;
    return dir?.FullName ?? throw new InvalidOperationException("run from the exercise folder");
}
