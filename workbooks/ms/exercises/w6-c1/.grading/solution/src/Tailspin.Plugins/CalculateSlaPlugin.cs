using System;
using Microsoft.Xrm.Sdk;

namespace Tailspin.Plugins
{
    /// <summary>
    /// Main-operation plug-in for the contoso_CalculateSla custom API (an unbound Action).
    /// </summary>
    public class CalculateSlaPlugin : IPlugin
    {
        public const string MessageName = "contoso_CalculateSla";

        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));

            if (context.MessageName != MessageName || context.Stage != 30)
            {
                tracing.Trace("CalculateSlaPlugin: not the {0} main operation (message {1}, stage {2}).",
                    MessageName, context.MessageName, context.Stage);
                return;
            }

            if (!context.InputParameters.Contains("Priority") || !(context.InputParameters["Priority"] is int))
            {
                throw new InvalidPluginExecutionException("Priority is required (1-4).");
            }
            var priority = (int)context.InputParameters["Priority"];
            if (priority < 1 || priority > 4)
            {
                throw new InvalidPluginExecutionException("Priority must be between 1 and 4.");
            }

            if (!context.InputParameters.Contains("CreatedOn") || !(context.InputParameters["CreatedOn"] is DateTime))
            {
                throw new InvalidPluginExecutionException("CreatedOn is required.");
            }
            var createdOn = DateTime.SpecifyKind(((DateTime)context.InputParameters["CreatedOn"]).ToUniversalTime(), DateTimeKind.Utc);
            var now = context.OperationCreatedOn;
            if (createdOn > now)
            {
                throw new InvalidPluginExecutionException("CreatedOn cannot be in the future.");
            }

            var region = context.InputParameters.Contains("RegionCode") ? context.InputParameters["RegionCode"] as string : null;
            var hours = SlaHoursFor(priority, region);
            var due = DateTime.SpecifyKind(createdOn.AddHours(hours), DateTimeKind.Utc);

            context.OutputParameters["SlaHours"] = hours;
            context.OutputParameters["DueOn"] = due;
            context.OutputParameters["IsBreached"] = now > due;
            tracing.Trace("SLA: priority {0}, region {1}, {2}h, due {3:o}", priority, region ?? "(none)", hours, due);
        }

        public static int SlaHoursFor(int priority, string regionCode)
        {
            int hours;
            switch (priority)
            {
                case 1: hours = 4; break;
                case 2: hours = 8; break;
                case 3: hours = 24; break;
                case 4: hours = 72; break;
                default: throw new InvalidPluginExecutionException("Priority must be between 1 and 4.");
            }
            var r = (regionCode ?? string.Empty).Trim().ToUpperInvariant();
            if (r == "AK" || r == "HI") hours += 24;
            return hours;
        }
    }
}
