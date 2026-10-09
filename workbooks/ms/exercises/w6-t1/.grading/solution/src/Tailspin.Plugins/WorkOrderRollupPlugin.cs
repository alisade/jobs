using System;
using Microsoft.Xrm.Sdk;

namespace Tailspin.Plugins
{
    /// <summary>
    /// Keeps contoso_totalcost = labor hours * labor rate + parts cost and stamps contoso_lastcalculatedon.
    /// Registration: Update of contoso_workorder, PreOperation (20), Synchronous,
    /// filtering attributes contoso_laborhours, contoso_laborrate, contoso_partscost,
    /// pre-image "PreImage" with the same three columns.
    /// The derived values are set on the Target, so the main operation writes them in the same
    /// database write: no second Update, so no re-entry into the pipeline.
    /// </summary>
    public class WorkOrderRollupPlugin : IPlugin
    {
        public const string PreImageAlias = "PreImage";

        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));

            tracing.Trace("WorkOrderRollupPlugin: Message={0} Stage={1} Depth={2} Id={3} CorrelationId={4}",
                context.MessageName, context.Stage, context.Depth, context.PrimaryEntityId, context.CorrelationId);

            if (context.Stage != 20)
            {
                throw new InvalidPluginExecutionException("WorkOrderRollupPlugin must be registered on PreOperation (20).");
            }

            var target = context.InputParameters["Target"] as Entity;
            if (target == null) return;

            Entity pre = context.PreEntityImages.Contains(PreImageAlias) ? context.PreEntityImages[PreImageAlias] : new Entity(WorkOrder.EntityName);

            var hours = Pick<decimal?>(target, pre, WorkOrder.LaborHours) ?? 0m;
            var rate = Pick<Money>(target, pre, WorkOrder.LaborRate);
            var parts = Pick<Money>(target, pre, WorkOrder.PartsCost);
            var total = hours * (rate != null ? rate.Value : 0m) + (parts != null ? parts.Value : 0m);

            target[WorkOrder.TotalCost] = new Money(total);
            target[WorkOrder.LastCalculatedOn] = context.OperationCreatedOn;
            tracing.Trace("Total cost set on Target: {0:0.00}", total);
        }

        // Changed value from the Target if present (even if null), else the value before the save.
        private static T Pick<T>(Entity target, Entity pre, string column)
        {
            return target.Contains(column) ? target.GetAttributeValue<T>(column) : pre.GetAttributeValue<T>(column);
        }
    }
}
