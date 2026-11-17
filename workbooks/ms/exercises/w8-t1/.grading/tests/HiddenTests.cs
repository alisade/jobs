using Dataverse.Sim;
using Microsoft.Xrm.Sdk;
using Xunit;

namespace Fabrikam.Plugins.Tests;

public class HiddenTransactionTests
{
    [Fact]
    public void Audit_row_is_linked_to_the_created_order()
    {
        var s = new Scenario();
        Assert.Null(s.Submit(Scenario.NewOrder("SO-1", Scenario.Contoso, 1_000m)));
        var order = Assert.Single(s.Orders);
        var audit = Assert.Single(s.Audits);
        Assert.Equal(order.Id, audit.GetAttributeValue<EntityReference>(CreditAudit.OrderId)?.Id);
        Assert.Equal("Approved", audit.GetAttributeValue<string>(CreditAudit.Decision));
        Assert.Equal(1_000m, audit.GetAttributeValue<Money>(CreditAudit.Amount).Value);
        Assert.Equal("SO-1", audit.GetAttributeValue<string>(CreditAudit.OrderNumber));
    }

    [Fact]
    public void Available_credit_is_recorded_on_the_audit_row()
    {
        var s = new Scenario();
        s.Submit(Scenario.NewOrder("SO-2", Scenario.Northwind, 2_000m));
        var audit = Assert.Single(s.Audits);
        Assert.Equal(25_000m, audit.GetAttributeValue<Money>(CreditAudit.Available).Value);
    }

    [Fact]
    public void Price_list_rejection_still_rejects_and_leaves_nothing()
    {
        var s = new Scenario();
        var ex = s.Submit(Scenario.NewOrder("SO-3", Scenario.Northwind, 8_900m, expiredPriceList: true));
        Assert.IsType<InvalidPluginExecutionException>(ex);
        Assert.Contains("Price list", ex!.Message);
        Assert.Empty(s.Orders);
        Assert.Empty(s.Audits);
    }

    [Fact]
    public void Credit_decline_still_rejects_early_and_leaves_nothing()
    {
        var s = new Scenario();
        var ex = s.Submit(Scenario.NewOrder("SO-4", Scenario.Litware, 52_000m));
        Assert.IsType<InvalidPluginExecutionException>(ex);
        Assert.Contains("Credit limit exceeded", ex!.Message);
        Assert.Empty(s.Orders);
        Assert.Empty(s.Audits);
        // Cancelled before the transaction-bound validation runs.
        Assert.DoesNotContain(s.Pipeline.Traces, t => t.TypeName == "Fabrikam.Plugins.OrderValidationPlugin");
    }

    [Fact]
    public void No_writes_happen_outside_the_transaction()
    {
        var s = new Scenario();
        s.Submit(Scenario.NewOrder("SO-5", Scenario.Contoso, 500m));
        s.Submit(Scenario.NewOrder("SO-6", Scenario.Contoso, 500m, expiredPriceList: true));
        Assert.DoesNotContain(s.Pipeline.Calls, c => c.CallerPluginType != null && c.CallerStage == 10 && c.Message is "Create" or "Update" or "Delete");
    }

    [Fact]
    public void Ledger_reconciles_with_orders_for_a_mixed_day()
    {
        var s = new Scenario();
        s.Submit(Scenario.NewOrder("SO-58001", Scenario.Contoso, 12_400m));
        s.Submit(Scenario.NewOrder("SO-58002", Scenario.Northwind, 8_900m, expiredPriceList: true));
        s.Submit(Scenario.NewOrder("SO-58003", Scenario.Litware, 52_000m));
        s.Submit(Scenario.NewOrder("SO-58004", Scenario.Northwind, 8_900m));
        var orderIds = s.Orders.Select(o => o.Id).ToHashSet();
        Assert.Equal(2, orderIds.Count);
        Assert.Equal(orderIds.Count, s.Audits.Count);
        Assert.All(s.Audits, a => Assert.Contains(a.GetAttributeValue<EntityReference>(CreditAudit.OrderId)!.Id, orderIds));
        Assert.Equal(s.Orders.Sum(o => o.GetAttributeValue<Money>(Order.Amount).Value),
                     s.Audits.Sum(a => a.GetAttributeValue<Money>(CreditAudit.Amount).Value));
    }
}

public class HiddenRegistrationTests
{
    private static RegistrationFile Reg() => RegistrationFile.Load(Repo.PathOf("registration/steps.json"));

    [Fact]
    public void Registration_passes_platform_rules()
    {
        Assert.Empty(Reg().Validate());
    }

    [Fact]
    public void Credit_validation_happens_before_the_main_operation()
    {
        var s = Assert.Single(Reg().Steps, x => x.PluginType == "Fabrikam.Plugins.CreditCheckPlugin");
        Assert.True(s.Stage == 10 || s.Stage == 20, "credit check must still be able to cancel the create");
        Assert.False(s.IsAsync);
    }

    [Fact]
    public void Audit_is_written_by_a_post_operation_step()
    {
        var reg = Reg();
        var post = reg.Steps.Where(x => x.Stage == 40 && x.Message.Equals("Create", StringComparison.OrdinalIgnoreCase)
            && x.PrimaryEntity == "contoso_order" && x.PluginType != "Fabrikam.Plugins.ShippingQuotePlugin").ToList();
        Assert.NotEmpty(post);
    }

    [Fact]
    public void Shipping_quote_step_left_alone()
    {
        var s = Assert.Single(Reg().Steps, x => x.PluginType == "Fabrikam.Plugins.ShippingQuotePlugin");
        Assert.True(s.IsAsync);
        Assert.Equal(40, s.Stage);
    }

    [Fact]
    public void Answer_names_the_transaction_boundary()
    {
        var text = File.ReadAllText(Repo.PathOf("ANSWER.md")).ToLowerInvariant();
        var root = text.Contains("## root cause") ? text[text.IndexOf("## root cause")..] : "";
        Assert.Contains("transaction", root);
        Assert.True(root.Contains("prevalidation") || root.Contains("pre-validation") || root.Contains("stage 10"));
    }
}
