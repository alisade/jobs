using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

namespace Tailspin.Plugins.Tests;

/// <summary>Collects ITracingService output so tests can assert on it.</summary>
public sealed class FakeTracing : ITracingService
{
    public List<string> Lines { get; } = new();
    public void Trace(string format, params object[] args) =>
        Lines.Add(args == null || args.Length == 0 ? format : string.Format(format, args));
    public string All => string.Join("\n", Lines);
}

/// <summary>Records every IOrganizationService call. A PreOperation plug-in should make none.</summary>
public sealed class RecordingOrgService : IOrganizationService
{
    public List<string> Calls { get; } = new();
    public Guid Create(Entity entity) { Calls.Add($"Create {entity.LogicalName}"); return Guid.NewGuid(); }
    public Entity Retrieve(string entityName, Guid id, ColumnSet columnSet) { Calls.Add($"Retrieve {entityName}"); return new Entity(entityName, id); }
    public void Update(Entity entity) => Calls.Add($"Update {entity.LogicalName}");
    public void Delete(string entityName, Guid id) => Calls.Add($"Delete {entityName}");
    public OrganizationResponse Execute(OrganizationRequest request) { Calls.Add($"Execute {request.RequestName}"); return new OrganizationResponse(); }
    public void Associate(string entityName, Guid entityId, Relationship relationship, EntityReferenceCollection relatedEntities) => Calls.Add("Associate");
    public void Disassociate(string entityName, Guid entityId, Relationship relationship, EntityReferenceCollection relatedEntities) => Calls.Add("Disassociate");
    public EntityCollection RetrieveMultiple(QueryBase query) { Calls.Add("RetrieveMultiple"); return new EntityCollection(); }
}

public sealed class FakeFactory : IOrganizationServiceFactory
{
    private readonly IOrganizationService _svc;
    public FakeFactory(IOrganizationService svc) => _svc = svc;
    public IOrganizationService CreateOrganizationService(Guid? userId) => _svc;
}

public sealed class FakeServiceProvider : IServiceProvider
{
    public RemoteExecutionContext Context { get; }
    public FakeTracing Tracing { get; } = new();
    public RecordingOrgService Service { get; } = new();

    public FakeServiceProvider(RemoteExecutionContext context) => Context = context;

    public object GetService(Type serviceType)
    {
        if (serviceType == typeof(IPluginExecutionContext) || serviceType == typeof(IExecutionContext)) return Context;
        if (serviceType == typeof(ITracingService)) return Tracing;
        if (serviceType == typeof(IOrganizationServiceFactory)) return new FakeFactory(Service);
        return null!;
    }
}

/// <summary>Builds execution contexts the way the Dataverse pipeline would hand them to a plug-in.</summary>
public static class Ctx
{
    public static readonly DateTime Now = new(2026, 10, 14, 15, 30, 0, DateTimeKind.Utc);

    public static Entity Target(int? status, params (string Name, object Value)[] extra)
    {
        var e = new Entity(WorkOrder.EntityName, Guid.Parse("6f0d2a8e-1c3b-4f6a-9d7e-2b5c8a1e4f90"));
        if (status.HasValue) e[WorkOrder.Status] = new OptionSetValue(status.Value);
        foreach (var (name, value) in extra) e[name] = value;
        return e;
    }

    public static Entity PreImage(int status, DateTime? actualStart = null, string? notes = null)
    {
        var e = new Entity(WorkOrder.EntityName, Guid.Parse("6f0d2a8e-1c3b-4f6a-9d7e-2b5c8a1e4f90"));
        e[WorkOrder.Status] = new OptionSetValue(status);
        if (actualStart.HasValue) e[WorkOrder.ActualStart] = actualStart.Value;
        if (notes != null) e[WorkOrder.ResolutionNotes] = notes;
        return e;
    }

    public static RemoteExecutionContext Update(Entity target, Entity? preImage, int stage = 20, int depth = 1,
        string message = "Update", string? entity = null, string preImageAlias = "PreImage")
    {
        var ctx = new RemoteExecutionContext
        {
            MessageName = message,
            PrimaryEntityName = entity ?? target.LogicalName,
            PrimaryEntityId = target.Id,
            Stage = stage,
            Mode = 0,
            Depth = depth,
            CorrelationId = Guid.Parse("a1b2c3d4-0000-4000-8000-00000000c0de"),
            UserId = Guid.Parse("11111111-2222-3333-4444-555555555555"),
            InitiatingUserId = Guid.Parse("11111111-2222-3333-4444-555555555555"),
            OrganizationName = "tailspin-uat",
            OperationCreatedOn = Now,
            IsInTransaction = stage != 10,
        };
        ctx.InputParameters["Target"] = target;
        if (preImage != null) ctx.PreEntityImages[preImageAlias] = preImage;
        return ctx;
    }

    public static RemoteExecutionContext CustomApi(int stage = 30, string message = "contoso_CalculateSla")
    {
        return new RemoteExecutionContext
        {
            MessageName = message,
            PrimaryEntityName = "none",
            Stage = stage,
            Mode = 0,
            Depth = 1,
            CorrelationId = Guid.NewGuid(),
            OperationCreatedOn = Now,
        };
    }

    public static FakeServiceProvider Run(IPlugin plugin, RemoteExecutionContext ctx)
    {
        var sp = new FakeServiceProvider(ctx);
        plugin.Execute(sp);
        return sp;
    }
}

/// <summary>Finds files relative to the exercise root (the folder containing registration/).</summary>
public static class Repo
{
    public static string PathOf(string relative)
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null && !Directory.Exists(System.IO.Path.Combine(dir.FullName, "registration")))
            dir = dir.Parent;
        if (dir == null) throw new InvalidOperationException("Could not find the exercise root (registration/ folder).");
        return System.IO.Path.Combine(dir.FullName, relative);
    }
}
