using System.Text.Json;
using Microsoft.Xrm.Sdk;
using Xunit;

namespace Tailspin.Plugins.Tests;

public class HiddenStatusTests
{
    private static FakeServiceProvider Run(Entity target, Entity? pre, int stage = 20, int depth = 1, string? entity = null) =>
        Ctx.Run(new WorkOrderStatusPlugin(), Ctx.Update(target, pre, stage, depth, entity: entity));

    [Theory]
    [InlineData(WorkOrder.New, WorkOrder.Scheduled)]
    [InlineData(WorkOrder.New, WorkOrder.Cancelled)]
    [InlineData(WorkOrder.Scheduled, WorkOrder.InProgress)]
    [InlineData(WorkOrder.Scheduled, WorkOrder.OnHold)]
    [InlineData(WorkOrder.Scheduled, WorkOrder.Cancelled)]
    [InlineData(WorkOrder.InProgress, WorkOrder.OnHold)]
    [InlineData(WorkOrder.OnHold, WorkOrder.Scheduled)]
    [InlineData(WorkOrder.OnHold, WorkOrder.InProgress)]
    [InlineData(WorkOrder.OnHold, WorkOrder.Cancelled)]
    public void Allowed_transitions_pass(int from, int to)
    {
        var target = Ctx.Target(to);
        Run(target, Ctx.PreImage(from));
        Assert.Equal(Ctx.Now, target.GetAttributeValue<DateTime>(WorkOrder.StatusChangedOn));
    }

    [Theory]
    [InlineData(WorkOrder.New, WorkOrder.Completed)]
    [InlineData(WorkOrder.New, WorkOrder.InProgress)]
    [InlineData(WorkOrder.Completed, WorkOrder.InProgress)]
    [InlineData(WorkOrder.Cancelled, WorkOrder.Scheduled)]
    [InlineData(WorkOrder.InProgress, WorkOrder.New)]
    [InlineData(WorkOrder.InProgress, WorkOrder.Cancelled)]
    public void Illegal_transitions_throw_user_friendly(int from, int to)
    {
        var ex = Assert.Throws<InvalidPluginExecutionException>(() => Run(Ctx.Target(to), Ctx.PreImage(from)));
        Assert.Contains(WorkOrder.Labels[from], ex.Message);
        Assert.Contains(WorkOrder.Labels[to], ex.Message);
        Assert.DoesNotContain("100000", ex.Message);
    }

    [Fact]
    public void Same_status_is_a_no_op()
    {
        var target = Ctx.Target(WorkOrder.Completed);
        Run(target, Ctx.PreImage(WorkOrder.Completed, Ctx.Now.AddHours(-3), "done"));
        Assert.False(target.Contains(WorkOrder.StatusChangedOn));
        Assert.False(target.Contains(WorkOrder.CompletedOn));
    }

    [Fact]
    public void Missing_pre_image_is_a_registration_error()
    {
        var ex = Assert.Throws<InvalidPluginExecutionException>(() => Run(Ctx.Target(WorkOrder.Scheduled), null));
        Assert.Contains("PreImage", ex.Message);
    }

    [Fact]
    public void Target_without_status_exits_early()
    {
        var target = Ctx.Target(null, (WorkOrder.ResolutionNotes, "updated notes only"));
        var sp = Run(target, null);
        Assert.Single(target.Attributes); // only resolution notes; nothing stamped
        Assert.Empty(sp.Service.Calls);
    }

    [Fact]
    public void Clearing_status_is_rejected()
    {
        var target = Ctx.Target(null);
        target[WorkOrder.Status] = null;
        Assert.Throws<InvalidPluginExecutionException>(() => Run(target, Ctx.PreImage(WorkOrder.Scheduled)));
    }

    [Fact]
    public void Validation_still_runs_at_depth_2()
    {
        // A flow or another plug-in updating the row arrives with Depth 2. Skipping validation on Depth
        // would let any automation bypass the rules (and Learn says not to build logic on Depth).
        Assert.Throws<InvalidPluginExecutionException>(() =>
            Run(Ctx.Target(WorkOrder.InProgress), Ctx.PreImage(WorkOrder.Completed), depth: 2));
    }

    [Fact]
    public void Wrong_stage_throws_instead_of_silently_doing_nothing()
    {
        Assert.Throws<InvalidPluginExecutionException>(() =>
            Run(Ctx.Target(WorkOrder.Scheduled), Ctx.PreImage(WorkOrder.New), stage: 40));
    }

    [Fact]
    public void Wrong_entity_is_ignored()
    {
        var target = new Entity("account", Guid.NewGuid());
        target[WorkOrder.Status] = new OptionSetValue(WorkOrder.Completed);
        var sp = Ctx.Run(new WorkOrderStatusPlugin(), Ctx.Update(target, Ctx.PreImage(WorkOrder.New), entity: "account"));
        Assert.Single(target.Attributes);
    }

    [Fact]
    public void Completing_requires_resolution_notes()
    {
        var ex = Assert.Throws<InvalidPluginExecutionException>(() =>
            Run(Ctx.Target(WorkOrder.Completed), Ctx.PreImage(WorkOrder.InProgress, Ctx.Now.AddHours(-1), "  ")));
        Assert.Contains("resolution", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void Completing_with_notes_in_target_stamps_completion_and_duration()
    {
        var target = Ctx.Target(WorkOrder.Completed, (WorkOrder.ResolutionNotes, "Replaced compressor"));
        Run(target, Ctx.PreImage(WorkOrder.InProgress, Ctx.Now.AddMinutes(-135)));
        Assert.Equal(Ctx.Now, target.GetAttributeValue<DateTime>(WorkOrder.CompletedOn));
        Assert.Equal(135, target.GetAttributeValue<int>(WorkOrder.DurationMinutes));
    }

    [Fact]
    public void Completing_with_notes_in_pre_image_is_fine()
    {
        var target = Ctx.Target(WorkOrder.Completed);
        Run(target, Ctx.PreImage(WorkOrder.InProgress, Ctx.Now.AddMinutes(-61).AddSeconds(-30), "Reset breaker"));
        Assert.Equal(61, target.GetAttributeValue<int>(WorkOrder.DurationMinutes));
    }

    [Fact]
    public void Resume_does_not_overwrite_existing_actual_start()
    {
        var target = Ctx.Target(WorkOrder.InProgress);
        Run(target, Ctx.PreImage(WorkOrder.OnHold, Ctx.Now.AddDays(-1)));
        Assert.False(target.Contains(WorkOrder.ActualStart));
    }

    [Fact]
    public void Plugin_makes_no_organization_service_calls()
    {
        var target = Ctx.Target(WorkOrder.Completed, (WorkOrder.ResolutionNotes, "ok"));
        var sp = Run(target, Ctx.PreImage(WorkOrder.InProgress, Ctx.Now.AddHours(-2)));
        Assert.Empty(sp.Service.Calls);
    }

    [Fact]
    public void Trace_includes_depth_and_correlation_id()
    {
        var sp = Run(Ctx.Target(WorkOrder.Scheduled), Ctx.PreImage(WorkOrder.New));
        Assert.Contains("a1b2c3d4-0000-4000-8000-00000000c0de", sp.Tracing.All);
        Assert.Contains("Depth", sp.Tracing.All);
    }
}

public class HiddenSlaTests
{
    private static RemoteExecutionContext Call(object? priority, DateTime? created, string? region, int stage = 30, string message = "contoso_CalculateSla")
    {
        var ctx = Ctx.CustomApi(stage, message);
        if (priority != null) ctx.InputParameters["Priority"] = priority;
        if (created.HasValue) ctx.InputParameters["CreatedOn"] = created.Value;
        if (region != null) ctx.InputParameters["RegionCode"] = region;
        Ctx.Run(new CalculateSlaPlugin(), ctx);
        return ctx;
    }

    [Theory]
    [InlineData(1, null, 4)]
    [InlineData(3, "TX", 24)]
    [InlineData(4, "AK", 96)]
    [InlineData(2, "hi", 32)]
    public void Sla_hours_table(int priority, string? region, int hours)
    {
        Assert.Equal(hours, CalculateSlaPlugin.SlaHoursFor(priority, region!));
        var ctx = Call(priority, Ctx.Now.AddHours(-1), region);
        Assert.Equal(hours, ctx.OutputParameters["SlaHours"]);
    }

    [Fact]
    public void Output_types_match_the_custom_api_definition()
    {
        var ctx = Call(1, Ctx.Now.AddHours(-1), null);
        Assert.IsType<DateTime>(ctx.OutputParameters["DueOn"]);
        Assert.Equal(DateTimeKind.Utc, ((DateTime)ctx.OutputParameters["DueOn"]).Kind);
        Assert.IsType<int>(ctx.OutputParameters["SlaHours"]);
        Assert.IsType<bool>(ctx.OutputParameters["IsBreached"]);
    }

    [Fact]
    public void Breached_when_now_is_past_due()
    {
        var ctx = Call(1, Ctx.Now.AddHours(-5), "WA");
        Assert.Equal(true, ctx.OutputParameters["IsBreached"]);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(5)]
    public void Out_of_range_priority_is_rejected(int priority) =>
        Assert.Throws<InvalidPluginExecutionException>(() => Call(priority, Ctx.Now.AddHours(-1), null));

    [Fact]
    public void Missing_priority_is_rejected() =>
        Assert.Throws<InvalidPluginExecutionException>(() => Call(null, Ctx.Now.AddHours(-1), null));

    [Fact]
    public void Created_on_in_the_future_is_rejected() =>
        Assert.Throws<InvalidPluginExecutionException>(() => Call(2, Ctx.Now.AddHours(3), null));

    [Fact]
    public void Wrong_stage_or_message_sets_no_outputs()
    {
        Assert.Empty(Call(2, Ctx.Now.AddHours(-1), null, stage: 40).OutputParameters);
        Assert.Empty(Call(2, Ctx.Now.AddHours(-1), null, message: "contoso_Other").OutputParameters);
    }
}

public class HiddenRegistrationTests
{
    private static JsonElement Step()
    {
        var doc = JsonDocument.Parse(File.ReadAllText(Repo.PathOf("registration/steps.json")));
        return doc.RootElement.GetProperty("steps")[0];
    }

    private static JsonElement Api() =>
        JsonDocument.Parse(File.ReadAllText(Repo.PathOf("registration/customapi.json"))).RootElement;

    private static List<string> Strings(JsonElement arr) =>
        arr.EnumerateArray().Select(x => x.GetString()!.Trim().ToLowerInvariant()).ToList();

    [Fact]
    public void Step_is_pre_operation_synchronous()
    {
        var s = Step();
        Assert.Equal(20, s.GetProperty("stage").GetInt32());
        Assert.Equal("synchronous", s.GetProperty("mode").GetString()!.ToLowerInvariant());
    }

    [Fact]
    public void Filtering_attributes_are_status_only()
    {
        var attrs = Strings(Step().GetProperty("filteringAttributes"));
        Assert.Equal(new[] { WorkOrder.Status }, attrs.ToArray());
        Assert.DoesNotContain(WorkOrder.PrimaryKey, attrs);
    }

    [Fact]
    public void Single_pre_image_with_only_needed_columns()
    {
        var images = Step().GetProperty("images").EnumerateArray().ToList();
        Assert.Single(images);
        var img = images[0];
        Assert.Equal("preimage", img.GetProperty("type").GetString()!.ToLowerInvariant());
        Assert.Equal("PreImage", img.GetProperty("alias").GetString());
        var cols = Strings(img.GetProperty("attributes")).OrderBy(x => x).ToArray();
        Assert.Equal(new[] { WorkOrder.ActualStart, WorkOrder.ResolutionNotes, WorkOrder.Status }.OrderBy(x => x).ToArray(), cols);
    }

    [Fact]
    public void Custom_api_is_a_global_action_callable_from_flows()
    {
        var a = Api();
        Assert.Equal(JsonValueKind.False, a.GetProperty("isFunction").ValueKind);
        Assert.Equal("global", a.GetProperty("bindingType").GetString()!.ToLowerInvariant());
        Assert.Equal("none", a.GetProperty("allowedCustomProcessingStepType").GetString()!.ToLowerInvariant());
    }

    [Fact]
    public void Custom_api_parameters_and_properties()
    {
        var a = Api();
        var req = a.GetProperty("requestParameters").EnumerateArray()
            .ToDictionary(p => p.GetProperty("uniqueName").GetString()!, p => p);
        Assert.Equal("Integer", req["Priority"].GetProperty("type").GetString());
        Assert.False(req["Priority"].GetProperty("isOptional").GetBoolean());
        Assert.Equal("DateTime", req["CreatedOn"].GetProperty("type").GetString());
        Assert.False(req["CreatedOn"].GetProperty("isOptional").GetBoolean());
        Assert.Equal("String", req["RegionCode"].GetProperty("type").GetString());
        Assert.True(req["RegionCode"].GetProperty("isOptional").GetBoolean());
        Assert.Equal(3, req.Count);

        var resp = a.GetProperty("responseProperties").EnumerateArray()
            .ToDictionary(p => p.GetProperty("uniqueName").GetString()!, p => p.GetProperty("type").GetString());
        Assert.Equal("DateTime", resp["DueOn"]);
        Assert.Equal("Integer", resp["SlaHours"]);
        Assert.Equal("Boolean", resp["IsBreached"]);
        Assert.Equal(3, resp.Count);
    }
}
