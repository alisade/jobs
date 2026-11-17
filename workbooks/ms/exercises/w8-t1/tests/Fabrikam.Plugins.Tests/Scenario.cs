using Dataverse.Sim;
using Microsoft.Xrm.Sdk;
using Fabrikam.Plugins;

namespace Fabrikam.Plugins.Tests;

/// <summary>Simulated Fabrikam org with three customers, using registration/steps.json.</summary>
public sealed class Scenario
{
    public static readonly Guid Contoso = Guid.Parse("0a6f3c1e-2b4d-4e8f-9a1c-3d5e7f9b1c2d");
    public static readonly Guid Northwind = Guid.Parse("1b7e4d2f-3c5e-4f9a-8b2d-4e6f8a0c2d3e");
    public static readonly Guid Litware = Guid.Parse("2c8f5e3a-4d6f-4a0b-9c3e-5f7a9b1d3e4f");

    public Pipeline Pipeline { get; }
    public RegistrationFile Registration { get; }

    public Scenario()
    {
        Registration = RegistrationFile.Load(Repo.PathOf("registration/steps.json"));
        Pipeline = new Pipeline(typeof(CreditCheckPlugin).Assembly, Registration.Steps)
        {
            OrganizationName = "fabrikam-prod",
            Clock = new DateTime(2026, 10, 2, 9, 15, 0, DateTimeKind.Utc),
        };
        Customer(Contoso, "Contoso Hospitality", 50_000m, 20_000m);
        Customer(Northwind, "Northwind Traders", 30_000m, 5_000m);
        Customer(Litware, "Litware Inc", 40_000m, 12_500m);
    }

    private void Customer(Guid id, string name, decimal limit, decimal open)
    {
        var a = new Entity(Account.EntityName, id);
        a[Account.Name] = name; a[Account.CreditLimit] = new Money(limit); a[Account.OpenBalance] = new Money(open);
        Pipeline.Seed(a);
    }

    public static Entity NewOrder(string number, Guid customer, decimal amount, bool expiredPriceList = false)
    {
        var o = new Entity(Order.EntityName);
        o[Order.Number] = number;
        o[Order.Customer] = new EntityReference(Account.EntityName, customer);
        o[Order.Amount] = new Money(amount);
        o[Order.PriceList] = expiredPriceList ? "FAB-2026Q3" : "FAB-2026Q4";
        o[Order.PriceListExpiresOn] = expiredPriceList
            ? new DateTime(2026, 9, 30, 23, 59, 59, DateTimeKind.Utc)
            : new DateTime(2026, 12, 31, 23, 59, 59, DateTimeKind.Utc);
        return o;
    }

    /// <summary>Submits an order the way the sales app does; returns the exception if the platform rejected it.</summary>
    public Exception? Submit(Entity order)
    {
        try { Pipeline.ClientService().Create(order); return null; }
        catch (Exception ex) { return ex; }
    }

    public List<Entity> Orders => Pipeline.All(Order.EntityName);
    public List<Entity> Audits => Pipeline.All(CreditAudit.EntityName);
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
