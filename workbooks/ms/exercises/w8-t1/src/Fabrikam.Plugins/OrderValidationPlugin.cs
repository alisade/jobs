using System;
using Microsoft.Xrm.Sdk;

namespace Fabrikam.Plugins
{
    /// <summary>Rejects orders priced from an expired price list (provided; not part of the fault).</summary>
    public class OrderValidationPlugin : IPlugin
    {
        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));
            var order = (Entity)context.InputParameters["Target"];
            var expires = order.GetAttributeValue<DateTime?>(Order.PriceListExpiresOn);
            tracing.Trace("OrderValidationPlugin: Stage={0} Order={1} PriceList={2} Expires={3:o}",
                context.Stage, order.GetAttributeValue<string>(Order.Number), order.GetAttributeValue<string>(Order.PriceList), expires);
            if (expires.HasValue && expires.Value < context.OperationCreatedOn)
            {
                throw new InvalidPluginExecutionException(string.Format(
                    "Price list {0} expired on {1:yyyy-MM-dd}. Refresh prices and resubmit the order.",
                    order.GetAttributeValue<string>(Order.PriceList), expires.Value));
            }
        }
    }
}
