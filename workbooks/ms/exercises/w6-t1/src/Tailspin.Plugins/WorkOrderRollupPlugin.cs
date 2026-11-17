using System;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

namespace Tailspin.Plugins
{
    /// <summary>
    /// Release 3.4.0 (2026-10-07): keeps contoso_totalcost = labor hours * labor rate + parts cost,
    /// and stamps contoso_lastcalculatedon, whenever a work order is saved.
    /// </summary>
    public class WorkOrderRollupPlugin : IPlugin
    {
        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));
            var factory = (IOrganizationServiceFactory)serviceProvider.GetService(typeof(IOrganizationServiceFactory));
            var service = factory.CreateOrganizationService(context.UserId);

            tracing.Trace("WorkOrderRollupPlugin: Message={0} Stage={1} Depth={2} Id={3} CorrelationId={4}",
                context.MessageName, context.Stage, context.Depth, context.PrimaryEntityId, context.CorrelationId);

            var row = service.Retrieve(WorkOrder.EntityName, context.PrimaryEntityId,
                new ColumnSet(WorkOrder.LaborHours, WorkOrder.LaborRate, WorkOrder.PartsCost));

            var hours = row.GetAttributeValue<decimal?>(WorkOrder.LaborHours) ?? 0m;
            var rate = row.GetAttributeValue<Money>(WorkOrder.LaborRate);
            var parts = row.GetAttributeValue<Money>(WorkOrder.PartsCost);
            var total = hours * (rate != null ? rate.Value : 0m) + (parts != null ? parts.Value : 0m);

            var update = new Entity(WorkOrder.EntityName, context.PrimaryEntityId);
            update[WorkOrder.TotalCost] = new Money(total);
            update[WorkOrder.LastCalculatedOn] = context.OperationCreatedOn;
            tracing.Trace("Writing total cost {0:0.00}", total);
            service.Update(update);
            tracing.Trace("WorkOrderRollupPlugin: done");
        }
    }
}
