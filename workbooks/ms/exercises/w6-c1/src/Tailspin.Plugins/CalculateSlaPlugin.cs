using System;
using Microsoft.Xrm.Sdk;

namespace Tailspin.Plugins
{
    /// <summary>
    /// Main-operation plug-in for the contoso_CalculateSla custom API.
    /// Request:  Priority (Integer, required), CreatedOn (DateTime, required), RegionCode (String, optional)
    /// Response: DueOn (DateTime), SlaHours (Integer), IsBreached (Boolean)
    /// </summary>
    public class CalculateSlaPlugin : IPlugin
    {
        public const string MessageName = "contoso_CalculateSla";

        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));

            // TODO: only act for MessageName at the main operation stage (30); otherwise trace and return.
            // TODO: validate inputs (see README) and throw InvalidPluginExecutionException on bad input.
            // TODO: set OutputParameters DueOn (UTC DateTime), SlaHours (int), IsBreached (bool).
            throw new NotImplementedException("CalculateSlaPlugin is not implemented yet.");
        }

        /// <summary>SLA hours for a priority and region (see README table).</summary>
        public static int SlaHoursFor(int priority, string regionCode)
        {
            // TODO
            throw new NotImplementedException();
        }
    }
}
