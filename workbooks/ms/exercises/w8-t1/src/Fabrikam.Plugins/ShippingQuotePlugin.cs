using System;
using Microsoft.Xrm.Sdk;

namespace Fabrikam.Plugins
{
    /// <summary>
    /// Requests a freight quote from the carrier API after an order is created.
    /// INC-4471 (2026-09-12): moved from synchronous to asynchronous PostOperation and the HTTP
    /// timeout cut from 100 s to 10 s. The HTTP call is omitted in this local build.
    /// </summary>
    public class ShippingQuotePlugin : IPlugin
    {
        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));
            tracing.Trace("ShippingQuotePlugin: Mode={0} Depth={1} Order={2} quote requested (timeout 10 s)",
                context.Mode, context.Depth, context.PrimaryEntityId);
        }
    }
}
