using Dataverse.Sim;
using Microsoft.Xrm.Sdk;
using Tailspin.Plugins;

namespace Tailspin.Plugins.Tests;

/// <summary>Builds a simulated Dataverse with the steps in registration/steps.json and one work order.</summary>
public sealed class Scenario
{
    public Pipeline Pipeline { get; }
    public RegistrationFile Registration { get; }
    public Guid WorkOrderId { get; } = Guid.Parse("3d6c1f0e-8a52-4b7e-9f13-0c4a5e2d7b61");

    public Scenario(decimal? hours = 2m, decimal? rate = 95m, decimal? parts = 140m)
    {
        Registration = RegistrationFile.Load(Repo.PathOf("registration/steps.json"));
        Pipeline = new Pipeline(typeof(WorkOrderRollupPlugin).Assembly, Registration.Steps) { OrganizationName = "tailspin-prod" };
        var wo = new Entity(WorkOrder.EntityName, WorkOrderId);
        wo[WorkOrder.Number] = "WO-10421";
        wo[WorkOrder.Description] = "Walk-in freezer not holding temperature";
        if (hours.HasValue) wo[WorkOrder.LaborHours] = hours.Value;
        if (rate.HasValue) wo[WorkOrder.LaborRate] = new Money(rate.Value);
        if (parts.HasValue) wo[WorkOrder.PartsCost] = new Money(parts.Value);
        Pipeline.Seed(wo);
    }

    /// <summary>Client save of the given columns (what the model-driven form sends: only changed columns).</summary>
    public void Save(params (string Name, object? Value)[] changes)
    {
        var e = new Entity(WorkOrder.EntityName, WorkOrderId);
        foreach (var (n, v) in changes) e[n] = v;
        Pipeline.ClientService().Update(e);
    }

    public Entity Row => Pipeline.Get(WorkOrder.EntityName, WorkOrderId)!;
    public decimal Total => Row.GetAttributeValue<Money>(WorkOrder.TotalCost)?.Value ?? -1m;
    public int MaxDepth => Pipeline.Traces.Count == 0 ? 0 : Pipeline.Traces.Max(t => t.Depth);
}

public static class Repo
{
    public static string PathOf(string relative)
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null && !Directory.Exists(Path.Combine(dir.FullName, "registration"))) dir = dir.Parent;
        if (dir == null) throw new InvalidOperationException("Could not find the exercise root (registration/ folder).");
        return Path.Combine(dir.FullName, relative);
    }
}
