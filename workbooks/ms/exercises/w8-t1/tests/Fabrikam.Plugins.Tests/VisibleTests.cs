using Xunit;

namespace Fabrikam.Plugins.Tests;

public class VisibleTests
{
    [Fact]
    public void Valid_order_gets_exactly_one_credit_audit_row()
    {
        var s = new Scenario();
        Assert.Null(s.Submit(Scenario.NewOrder("SO-58001", Scenario.Contoso, 12_400m)));
        Assert.Single(s.Orders);
        Assert.Single(s.Audits);
    }

    [Fact]
    public void Order_rejected_for_an_expired_price_list_leaves_no_audit_row()
    {
        var s = new Scenario();
        Assert.NotNull(s.Submit(Scenario.NewOrder("SO-58002", Scenario.Northwind, 8_900m, expiredPriceList: true)));
        Assert.Empty(s.Orders);
        Assert.Empty(s.Audits);
    }
}
