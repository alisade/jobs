using System.Text.Json;
using Microsoft.Xrm.Sdk;
using Xunit;

namespace Tailspin.Plugins.Tests;

public class VisibleTests
{
    [Fact]
    public void Schedule_new_work_order_stamps_status_changed_on()
    {
        var target = Ctx.Target(WorkOrder.Scheduled);
        var sp = Ctx.Run(new WorkOrderStatusPlugin(), Ctx.Update(target, Ctx.PreImage(WorkOrder.New)));
        Assert.Equal(Ctx.Now, target.GetAttributeValue<DateTime>(WorkOrder.StatusChangedOn));
    }

    [Fact]
    public void Start_work_sets_actual_start_when_empty()
    {
        var target = Ctx.Target(WorkOrder.InProgress);
        Ctx.Run(new WorkOrderStatusPlugin(), Ctx.Update(target, Ctx.PreImage(WorkOrder.Scheduled)));
        Assert.Equal(Ctx.Now, target.GetAttributeValue<DateTime>(WorkOrder.ActualStart));
    }

    [Fact]
    public void Transition_table_basics()
    {
        Assert.True(WorkOrderStatusPlugin.IsAllowed(WorkOrder.New, WorkOrder.Scheduled));
        Assert.False(WorkOrderStatusPlugin.IsAllowed(WorkOrder.Completed, WorkOrder.InProgress));
    }

    [Fact]
    public void Calculate_sla_priority_2()
    {
        var ctx = Ctx.CustomApi();
        var created = Ctx.Now.AddHours(-2);
        ctx.InputParameters["Priority"] = 2;
        ctx.InputParameters["CreatedOn"] = created;
        ctx.InputParameters["RegionCode"] = "WA";
        Ctx.Run(new CalculateSlaPlugin(), ctx);
        Assert.Equal(8, ctx.OutputParameters["SlaHours"]);
        Assert.Equal(created.AddHours(8), (DateTime)ctx.OutputParameters["DueOn"]);
        Assert.Equal(false, ctx.OutputParameters["IsBreached"]);
    }

    [Fact]
    public void Status_step_is_registered_pre_operation()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Repo.PathOf("registration/steps.json")));
        var step = doc.RootElement.GetProperty("steps")[0];
        Assert.Equal(20, step.GetProperty("stage").GetInt32());
    }
}
