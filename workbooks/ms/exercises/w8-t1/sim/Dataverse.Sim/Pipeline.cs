using System.Reflection;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

namespace Dataverse.Sim;

/// <summary>
/// Local stand-in for the Dataverse event execution pipeline. Models what matters for these exercises:
/// stages 10/20/30/40, sync vs async, filtering attributes, pre/post images, Depth with the
/// infinite-loop limit (8), and the database transaction: PreValidation of the initial operation runs
/// outside the transaction; 20 and 40 run inside it; any exception rolls the transaction back.
/// It is not a full Dataverse: no security, no RetrieveMultiple filters beyond simple equality.
/// </summary>
public sealed class Pipeline
{
    public int MaxDepth { get; set; } = 8;
    public string OrganizationName { get; set; } = "contoso-prod";
    public Guid UserId { get; set; } = Guid.Parse("5e1f2a3b-0c4d-4e5f-8a9b-1c2d3e4f5a6b");
    public DateTime Clock { get; set; } = new(2026, 10, 8, 14, 2, 11, DateTimeKind.Utc);
    public int DefaultCostMs { get; set; } = 3;

    public List<TraceRecord> Traces { get; } = new();
    public List<CallRecord> Calls { get; } = new();
    public IReadOnlyList<StepRegistration> Steps => _steps;

    private readonly Dictionary<string, Dictionary<Guid, Entity>> _store = new(StringComparer.OrdinalIgnoreCase);
    private readonly List<StepRegistration> _steps = new();
    private readonly Assembly _pluginAssembly;
    private readonly List<(StepRegistration Step, RemoteExecutionContext Ctx)> _asyncQueue = new();

    public Pipeline(Assembly pluginAssembly, IEnumerable<StepRegistration> steps)
    {
        _pluginAssembly = pluginAssembly;
        _steps.AddRange(steps.Where(s => s.Enabled));
    }

    // ---------- seed / inspect data (bypasses the pipeline) ----------
    public void Seed(Entity e)
    {
        Table(e.LogicalName)[e.Id] = Clone(e);
    }

    public Entity? Get(string entity, Guid id) => Table(entity).TryGetValue(id, out var e) ? Clone(e) : null;
    public List<Entity> All(string entity) => Table(entity).Values.Select(Clone).ToList();

    /// <summary>Advance simulated time (used for trace timestamps and OperationCreatedOn).</summary>
    public void Advance(int ms) => Clock = Clock.AddMilliseconds(ms);

    /// <summary>The service a client application (or the model-driven app) uses.</summary>
    public IOrganizationService ClientService(Guid? correlationId = null) =>
        new SimService(this, new CallerInfo(null, 0, 0, null, correlationId ?? Guid.NewGuid(), null));

    // ---------- core ----------
    internal sealed record CallerInfo(string? PluginType, int Stage, int Depth, Txn? Txn, Guid CorrelationId, Guid? RecordId);

    internal sealed class Txn
    {
        public Dictionary<string, Dictionary<Guid, Entity>> Snapshot { get; }
        public Txn(Dictionary<string, Dictionary<Guid, Entity>> snap) => Snapshot = snap;
    }

    private Dictionary<Guid, Entity> Table(string name)
    {
        if (!_store.TryGetValue(name, out var t)) { t = new Dictionary<Guid, Entity>(); _store[name] = t; }
        return t;
    }

    private Dictionary<string, Dictionary<Guid, Entity>> TakeSnapshot() =>
        _store.ToDictionary(k => k.Key, v => v.Value.ToDictionary(x => x.Key, x => Clone(x.Value)), StringComparer.OrdinalIgnoreCase);

    private void Restore(Txn txn)
    {
        _store.Clear();
        foreach (var kv in txn.Snapshot) _store[kv.Key] = kv.Value;
    }

    internal static Entity Clone(Entity e)
    {
        var c = new Entity(e.LogicalName, e.Id);
        foreach (var a in e.Attributes) c[a.Key] = a.Value;
        return c;
    }

    private static Entity Project(Entity e, IList<string> cols)
    {
        if (cols.Count == 0) return Clone(e);
        var c = new Entity(e.LogicalName, e.Id);
        foreach (var col in cols) if (e.Contains(col)) c[col] = e[col];
        return c;
    }

    internal Guid Execute(string message, Entity target, CallerInfo caller)
    {
        var depth = caller.Depth + 1;
        Calls.Add(new CallRecord
        {
            Message = message, Entity = target.LogicalName, Id = target.Id, Depth = depth,
            CallerPluginType = caller.PluginType, CallerStage = caller.Stage, CallerRecordId = caller.RecordId,
            Attributes = target.Attributes.Keys.ToList(),
        });
        if (depth > MaxDepth)
            throw new DataverseFault(DataverseFault.SdkCorrelationTokenDepthTooHigh, DataverseFault.LoopMessage);

        if (message == "Create" && target.Id == Guid.Empty) target.Id = Guid.NewGuid();
        if (message == "Update" && Get(target.LogicalName, target.Id) == null)
            throw new DataverseFault(unchecked((int)0x80040217), $"{target.LogicalName} With Id = {target.Id} Does Not Exist");

        var topLevel = caller.Txn == null;
        var shared10 = new ParameterCollection();
        var sharedMain = new ParameterCollection();
        var outputs = new ParameterCollection();
        var opTime = Clock;

        var steps = _steps.Where(s => Applies(s, message, target)).OrderBy(s => s.Stage).ThenBy(s => s.Rank).ToList();
        Entity? preState = message == "Create" ? null : Get(target.LogicalName, target.Id);

        // Stage 10: for the initial operation this runs before (outside) the transaction.
        foreach (var s in steps.Where(s => s.Stage == 10 && !s.IsAsync))
            RunStep(s, message, target, depth, caller.Txn, caller.CorrelationId, shared10, null, outputs, preState, null, opTime);

        var txn = caller.Txn ?? new Txn(TakeSnapshot());
        try
        {
            foreach (var s in steps.Where(s => s.Stage == 20 && !s.IsAsync))
                RunStep(s, message, target, depth, txn, caller.CorrelationId, sharedMain, shared10, outputs, preState, null, opTime);

            // Stage 30: main operation.
            Advance(DefaultCostMs);
            if (message == "Create")
            {
                Table(target.LogicalName)[target.Id] = Clone(target);
                outputs["id"] = target.Id;
            }
            else if (message == "Update")
            {
                var row = Table(target.LogicalName)[target.Id];
                foreach (var a in target.Attributes) row[a.Key] = a.Value;
            }
            else if (message == "Delete")
            {
                Table(target.LogicalName).Remove(target.Id);
            }

            var postState = message == "Delete" ? null : Get(target.LogicalName, target.Id);
            foreach (var s in steps.Where(s => s.Stage == 40 && !s.IsAsync))
                RunStep(s, message, target, depth, txn, caller.CorrelationId, sharedMain, shared10, outputs, preState, postState, opTime);

            foreach (var s in steps.Where(s => s.Stage == 40 && s.IsAsync))
                _asyncQueue.Add((s, BuildContext(s, message, Clone(target), depth, caller.CorrelationId, sharedMain, shared10, outputs, preState, postState, opTime, false)));
        }
        catch
        {
            if (topLevel) { Restore(txn); _asyncQueue.Clear(); }
            throw;
        }

        if (topLevel) DrainAsync();
        return target.Id;
    }

    private void DrainAsync()
    {
        while (_asyncQueue.Count > 0)
        {
            var (step, ctx) = _asyncQueue[0];
            _asyncQueue.RemoveAt(0);
            Advance(250); // the async service picks the job up later
            var txn = new Txn(TakeSnapshot());
            try { Invoke(step, ctx, txn); }
            catch (Exception) { Restore(txn); /* async failures land in the system job, not with the caller */ }
        }
    }

    private static bool Applies(StepRegistration s, string message, Entity target)
    {
        if (!s.Message.Equals(message, StringComparison.OrdinalIgnoreCase)) return false;
        if (!string.IsNullOrEmpty(s.PrimaryEntity) && !s.PrimaryEntity.Equals(target.LogicalName, StringComparison.OrdinalIgnoreCase)) return false;
        if (message == "Update" && s.FilteringAttributes.Count > 0)
            return s.FilteringAttributes.Any(a => target.Attributes.ContainsKey(a.Trim()));
        return true;
    }

    private RemoteExecutionContext BuildContext(StepRegistration s, string message, Entity target, int depth, Guid correlationId,
        ParameterCollection shared, ParameterCollection? parentShared, ParameterCollection outputs, Entity? pre, Entity? post,
        DateTime opTime, bool inTxn)
    {
        var ctx = new RemoteExecutionContext
        {
            MessageName = message,
            PrimaryEntityName = target.LogicalName,
            PrimaryEntityId = target.Id,
            Stage = s.Stage,
            Mode = s.IsAsync ? 1 : 0,
            Depth = depth,
            CorrelationId = correlationId,
            RequestId = Guid.NewGuid(),
            OperationId = Guid.NewGuid(),
            UserId = UserId,
            InitiatingUserId = UserId,
            OrganizationName = OrganizationName,
            OperationCreatedOn = opTime,
            IsInTransaction = inTxn,
        };
        ctx.InputParameters["Target"] = target;
        foreach (var kv in shared) ctx.SharedVariables[kv.Key] = kv.Value;
        if (parentShared != null)
        {
            // Learn: PreOperation/PostOperation read PreValidation shared variables from ParentContext.
            var parent = new RemoteExecutionContext { MessageName = message, PrimaryEntityName = target.LogicalName, Stage = 10, Depth = depth, CorrelationId = correlationId };
            foreach (var kv in parentShared) parent.SharedVariables[kv.Key] = kv.Value;
            ctx.ParentContext = parent;
        }
        if (s.Stage == 40) foreach (var kv in outputs) ctx.OutputParameters[kv.Key] = kv.Value;
        foreach (var img in s.Images)
        {
            if (img.Type.Equals("PreImage", StringComparison.OrdinalIgnoreCase) && pre != null && message != "Create")
                ctx.PreEntityImages[img.Alias] = Project(pre, img.Attributes);
            if (img.Type.Equals("PostImage", StringComparison.OrdinalIgnoreCase) && post != null && s.Stage == 40)
                ctx.PostEntityImages[img.Alias] = Project(post, img.Attributes);
        }
        return ctx;
    }

    private void RunStep(StepRegistration s, string message, Entity target, int depth, Txn? txn, Guid correlationId,
        ParameterCollection shared, ParameterCollection? parentShared, ParameterCollection outputs, Entity? pre, Entity? post, DateTime opTime)
    {
        var ctx = BuildContext(s, message, target, depth, correlationId, shared, parentShared, outputs, pre, post, opTime, txn != null);
        try { Invoke(s, ctx, txn); }
        finally { foreach (var kv in ctx.SharedVariables) shared[kv.Key] = kv.Value; }
    }

    private void Invoke(StepRegistration s, RemoteExecutionContext ctx, Txn? txn)
    {
        var type = _pluginAssembly.GetType(s.PluginType) ?? throw new InvalidOperationException("Plug-in type not found: " + s.PluginType);
        var ctor2 = type.GetConstructor(new[] { typeof(string), typeof(string) });
        var plugin = (IPlugin)(ctor2 != null ? ctor2.Invoke(new object?[] { s.UnsecureConfig, null }) : Activator.CreateInstance(type)!);

        var tracing = new SimTracing();
        var record = new TraceRecord
        {
            TypeName = s.PluginType, MessageName = ctx.MessageName, PrimaryEntity = ctx.PrimaryEntityName,
            Depth = ctx.Depth, Mode = ctx.Mode, Stage = ctx.Stage, CorrelationId = ctx.CorrelationId,
            RequestId = ctx.RequestId ?? Guid.Empty, PerformanceExecutionStartTime = Clock,
        };
        var start = Clock;
        var caller = new CallerInfo(s.PluginType, s.Stage, ctx.Depth, txn, ctx.CorrelationId, ctx.PrimaryEntityId);
        var sp = new SimServiceProvider(ctx, tracing, new SimFactory(this, caller));
        try
        {
            Advance(DefaultCostMs);
            plugin.Execute(sp);
        }
        catch (InvalidPluginExecutionException ex)
        {
            record.ExceptionDetails = $"Exception type: Microsoft.Xrm.Sdk.InvalidPluginExecutionException\nMessage: {ex.Message}\nErrorCode: {DataverseFault.IsvAborted} ({"0x" + DataverseFault.IsvAborted.ToString("x8")})";
            throw;
        }
        catch (DataverseFault ex)
        {
            record.ExceptionDetails = $"Exception type: System.ServiceModel.FaultException`1[Microsoft.Xrm.Sdk.OrganizationServiceFault]\nMessage: {ex.Message}\nErrorCode: {ex.ErrorCode} ({ex.HexCode})";
            throw;
        }
        catch (Exception ex)
        {
            record.ExceptionDetails = $"Unhandled exception: {ex.GetType().FullName}: {ex.Message}";
            throw new DataverseFault(DataverseFault.IsvUnexpected, "An unexpected error occurred from ISV code.", ex);
        }
        finally
        {
            record.MessageBlock = tracing.Text;
            record.PerformanceExecutionDuration = (int)(Clock - start).TotalMilliseconds;
            record.CreatedOn = Clock;
            Traces.Add(record);
        }
    }

    internal Entity RetrieveInternal(string entity, Guid id, ColumnSet cols, CallerInfo caller)
    {
        Calls.Add(new CallRecord { Message = "Retrieve", Entity = entity, Id = id, Depth = caller.Depth, CallerPluginType = caller.PluginType, CallerStage = caller.Stage, CallerRecordId = caller.RecordId });
        Advance(DefaultCostMs * 4);
        var e = Get(entity, id) ?? throw new DataverseFault(unchecked((int)0x80040217), $"{entity} With Id = {id} Does Not Exist");
        return cols.AllColumns ? e : Project(e, cols.Columns.ToList());
    }

    internal EntityCollection RetrieveMultipleInternal(QueryBase query, CallerInfo caller)
    {
        if (query is not QueryExpression q) throw new NotSupportedException("The simulator supports QueryExpression only.");
        Calls.Add(new CallRecord { Message = "RetrieveMultiple", Entity = q.EntityName, Depth = caller.Depth, CallerPluginType = caller.PluginType, CallerStage = caller.Stage, CallerRecordId = caller.RecordId });
        Advance(DefaultCostMs * 6);
        IEnumerable<Entity> rows = Table(q.EntityName).Values;
        foreach (var c in q.Criteria.Conditions)
        {
            if (c.Operator != ConditionOperator.Equal) throw new NotSupportedException("Only Equal conditions are simulated.");
            rows = rows.Where(r => r.Contains(c.AttributeName) && Equals(Norm(r[c.AttributeName]), Norm(c.Values[0])));
        }
        var result = new EntityCollection(rows.Select(r => q.ColumnSet.AllColumns ? Clone(r) : Project(r, q.ColumnSet.Columns.ToList())).ToList()) { EntityName = q.EntityName };
        return result;
    }

    private static object? Norm(object? v) => v switch
    {
        EntityReference er => er.Id,
        OptionSetValue o => o.Value,
        Money m => m.Value,
        _ => v,
    };
}

internal sealed class SimTracing : ITracingService
{
    private readonly List<string> _lines = new();
    public void Trace(string format, params object[] args) => _lines.Add(args == null || args.Length == 0 ? format : string.Format(format, args));
    public string Text => string.Join("\n", _lines);
}

internal sealed class SimServiceProvider : IServiceProvider
{
    private readonly RemoteExecutionContext _ctx; private readonly ITracingService _tr; private readonly IOrganizationServiceFactory _f;
    public SimServiceProvider(RemoteExecutionContext ctx, ITracingService tr, IOrganizationServiceFactory f) { _ctx = ctx; _tr = tr; _f = f; }
    public object? GetService(Type t) =>
        t == typeof(IPluginExecutionContext) || t == typeof(IExecutionContext) ? _ctx :
        t == typeof(ITracingService) ? _tr :
        t == typeof(IOrganizationServiceFactory) ? _f : null;
}

internal sealed class SimFactory : IOrganizationServiceFactory
{
    private readonly Pipeline _p; private readonly Pipeline.CallerInfo _c;
    public SimFactory(Pipeline p, Pipeline.CallerInfo c) { _p = p; _c = c; }
    public IOrganizationService CreateOrganizationService(Guid? userId) => new SimService(_p, _c);
}

internal sealed class SimService : IOrganizationService
{
    private readonly Pipeline _p; private readonly Pipeline.CallerInfo _c;
    public SimService(Pipeline p, Pipeline.CallerInfo c) { _p = p; _c = c; }
    public Guid Create(Entity entity) => _p.Execute("Create", Pipeline.Clone(entity), _c);
    public void Update(Entity entity) => _p.Execute("Update", Pipeline.Clone(entity), _c);
    public void Delete(string entityName, Guid id) => _p.Execute("Delete", new Entity(entityName, id), _c);
    public Entity Retrieve(string entityName, Guid id, ColumnSet columnSet) => _p.RetrieveInternal(entityName, id, columnSet, _c);
    public EntityCollection RetrieveMultiple(QueryBase query) => _p.RetrieveMultipleInternal(query, _c);
    public OrganizationResponse Execute(OrganizationRequest request) => throw new NotSupportedException("Execute is not simulated: " + request.RequestName);
    public void Associate(string entityName, Guid entityId, Relationship relationship, EntityReferenceCollection relatedEntities) => throw new NotSupportedException();
    public void Disassociate(string entityName, Guid entityId, Relationship relationship, EntityReferenceCollection relatedEntities) => throw new NotSupportedException();
}
