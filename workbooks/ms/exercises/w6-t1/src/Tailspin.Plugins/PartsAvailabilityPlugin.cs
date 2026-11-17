using System;
using Microsoft.Xrm.Sdk;

namespace Tailspin.Plugins
{
    /// <summary>
    /// Asynchronous PostOperation step: when the parts list changes, asks the Northwind Parts vendor API
    /// for availability and writes an ETA note. The HTTP call is omitted in this local build.
    /// </summary>
    public class PartsAvailabilityPlugin : IPlugin
    {
        private readonly string _endpoint;

        public PartsAvailabilityPlugin(string unsecureConfig, string secureConfig)
        {
            _endpoint = string.IsNullOrEmpty(unsecureConfig) ? "https://api.northwindparts.example/v2/availability" : unsecureConfig;
        }

        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));
            tracing.Trace("PartsAvailabilityPlugin: Depth={0} Id={1} calling {2}", context.Depth, context.PrimaryEntityId, _endpoint);
            // Real implementation: HttpClient with a 15 s timeout, GetAwaiter().GetResult(), then write an ETA note.
        }
    }
}
