using Microsoft.Xrm.Sdk;
using Xunit;

namespace Tailspin.Plugins.Tests;

public class VisibleTests
{
    [Fact]
    public void Saving_labor_hours_succeeds_and_rolls_up_total()
    {
        var s = new Scenario(hours: 2m, rate: 95m, parts: 140m);
        s.Save((WorkOrder.LaborHours, 3.5m));
        Assert.Equal(3.5m * 95m + 140m, s.Total);
    }

    [Fact]
    public void Registration_file_passes_registration_rules()
    {
        var s = new Scenario();
        Assert.Empty(s.Registration.Validate());
    }
}
