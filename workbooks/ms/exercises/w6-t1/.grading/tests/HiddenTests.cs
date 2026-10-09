using Dataverse.Sim;
using Microsoft.Xrm.Sdk;
using Xunit;

namespace Tailspin.Plugins.Tests;

public class HiddenPipelineTests
{
    private const string Rollup = "Tailspin.Plugins.WorkOrderRollupPlugin";

    [Theory]
    [InlineData(WorkOrder.LaborHours)]
    [InlineData(WorkOrder.LaborRate)]
    [InlineData(WorkOrder.PartsCost)]
    public void Depth_never_exceeds_two(string column)
    {
        var s = new Scenario();
        object value = column == WorkOrder.LaborHours ? 5m : new Money(200m);
        s.Save((column, value));
        Assert.True(s.Pipeline.Calls.Max(c => c.Depth) <= 2, "max depth " + s.Pipeline.Calls.Max(c => c.Depth));
    }

    [Fact]
    public void Parts_only_update_uses_stored_labor_and_rate()
    {
        var s = new Scenario(hours: 2m, rate: 95m, parts: 140m);
        s.Save((WorkOrder.PartsCost, new Money(310m)));
        Assert.Equal(2m * 95m + 310m, s.Total);
    }

    [Fact]
    public void Rate_and_hours_in_same_save()
    {
        var s = new Scenario(hours: 2m, rate: 95m, parts: 0m);
        s.Save((WorkOrder.LaborHours, 4m), (WorkOrder.LaborRate, new Money(120m)));
        Assert.Equal(480m, s.Total);
    }

    [Fact]
    public void Missing_parts_cost_counts_as_zero()
    {
        var s = new Scenario(hours: 1m, rate: 100m, parts: null);
        s.Save((WorkOrder.LaborHours, 1.5m));
        Assert.Equal(150m, s.Total);
    }

    [Fact]
    public void Last_calculated_on_is_the_operation_time()
    {
        var s = new Scenario();
        var opTime = s.Pipeline.Clock;
        s.Save((WorkOrder.LaborHours, 3m));
        Assert.Equal(opTime, s.Row.GetAttributeValue<DateTime>(WorkOrder.LastCalculatedOn));
    }

    [Fact]
    public void Description_only_save_does_not_run_the_rollup()
    {
        var s = new Scenario();
        s.Save((WorkOrder.Description, "typo fixed"));
        Assert.DoesNotContain(s.Pipeline.Traces, t => t.TypeName == Rollup);
        Assert.Equal("typo fixed", s.Row.GetAttributeValue<string>(WorkOrder.Description));
    }

    [Fact]
    public void Plugin_never_updates_the_triggering_record()
    {
        var s = new Scenario();
        s.Save((WorkOrder.LaborHours, 6m));
        Assert.DoesNotContain(s.Pipeline.Calls, c => c.Message == "Update" && c.CallerPluginType != null && c.Id == s.WorkOrderId);
    }

    [Fact]
    public void Plugin_does_not_retrieve_the_row_it_already_has()
    {
        var s = new Scenario();
        s.Save((WorkOrder.LaborHours, 6m));
        Assert.DoesNotContain(s.Pipeline.Calls, c => c.Message == "Retrieve" && c.CallerPluginType == Rollup);
    }
}

public class HiddenRegistrationTests
{
    private static StepRegistration RollupStep()
    {
        var reg = RegistrationFile.Load(Repo.PathOf("registration/steps.json"));
        return Assert.Single(reg.Steps, s => s.PluginType == "Tailspin.Plugins.WorkOrderRollupPlugin");
    }

    [Fact]
    public void Rollup_runs_pre_operation_synchronously()
    {
        var s = RollupStep();
        Assert.Equal(20, s.Stage);
        Assert.False(s.IsAsync);
    }

    [Fact]
    public void Rollup_filters_on_its_inputs_only()
    {
        var attrs = RollupStep().FilteringAttributes.Select(a => a.Trim().ToLowerInvariant()).OrderBy(a => a).ToArray();
        Assert.Equal(new[] { WorkOrder.LaborHours, WorkOrder.LaborRate, WorkOrder.PartsCost }.OrderBy(a => a).ToArray(), attrs);
    }

    [Fact]
    public void Rollup_pre_image_has_the_inputs_not_all_columns()
    {
        var img = Assert.Single(RollupStep().Images);
        Assert.Equal("preimage", img.Type.ToLowerInvariant());
        var cols = img.Attributes.Select(a => a.Trim().ToLowerInvariant()).ToList();
        Assert.NotEmpty(cols);
        Assert.Contains(WorkOrder.LaborHours, cols);
        Assert.Contains(WorkOrder.LaborRate, cols);
        Assert.Contains(WorkOrder.PartsCost, cols);
        Assert.True(cols.Count <= 4, "image should carry only the columns the plug-in reads");
    }

    [Fact]
    public void Parts_availability_step_left_alone()
    {
        var reg = RegistrationFile.Load(Repo.PathOf("registration/steps.json"));
        var s = Assert.Single(reg.Steps, x => x.PluginType == "Tailspin.Plugins.PartsAvailabilityPlugin");
        Assert.True(s.IsAsync);
        Assert.Equal(new[] { WorkOrder.PartsList }, s.FilteringAttributes.ToArray());
    }

    [Fact]
    public void Answer_names_the_loop_and_the_fix()
    {
        var text = File.ReadAllText(Repo.PathOf("ANSWER.md")).ToLowerInvariant();
        var root = text.Contains("## root cause") ? text[text.IndexOf("## root cause")..] : "";
        Assert.Contains("depth", root);
        Assert.True(root.Contains("filtering") || root.Contains("preoperation") || root.Contains("pre-operation"));
    }
}
