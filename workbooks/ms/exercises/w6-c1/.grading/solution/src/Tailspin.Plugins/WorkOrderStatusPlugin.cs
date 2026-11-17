using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Xrm.Sdk;

namespace Tailspin.Plugins
{
    /// <summary>
    /// Validates work order status transitions and stamps derived columns.
    /// Registration: Update of contoso_workorder, PreOperation (20), Synchronous,
    /// filtering attribute contoso_status, pre-image alias "PreImage"
    /// (contoso_status, contoso_actualstart, contoso_resolutionnotes).
    /// </summary>
    public class WorkOrderStatusPlugin : IPlugin
    {
        public const string PreImageAlias = "PreImage";

        public static readonly IDictionary<int, int[]> AllowedTransitions = new Dictionary<int, int[]>
        {
            { WorkOrder.New,        new[] { WorkOrder.Scheduled, WorkOrder.Cancelled } },
            { WorkOrder.Scheduled,  new[] { WorkOrder.InProgress, WorkOrder.OnHold, WorkOrder.Cancelled } },
            { WorkOrder.InProgress, new[] { WorkOrder.OnHold, WorkOrder.Completed } },
            { WorkOrder.OnHold,     new[] { WorkOrder.Scheduled, WorkOrder.InProgress, WorkOrder.Cancelled } },
            { WorkOrder.Completed,  new int[0] },
            { WorkOrder.Cancelled,  new int[0] },
        };

        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));

            tracing.Trace("WorkOrderStatusPlugin: Message={0} Entity={1} Stage={2} Depth={3} CorrelationId={4}",
                context.MessageName, context.PrimaryEntityName, context.Stage, context.Depth, context.CorrelationId);

            if (context.MessageName != "Update" || context.PrimaryEntityName != WorkOrder.EntityName)
            {
                tracing.Trace("Not registered for Update of {0}; nothing to do.", WorkOrder.EntityName);
                return;
            }

            // Setting Target values only takes effect before the main operation. In PostOperation the
            // assignments would be silently ignored, so fail loudly on a misregistration.
            if (context.Stage != 20)
            {
                throw new InvalidPluginExecutionException(
                    "WorkOrderStatusPlugin must be registered on the PreOperation (20) stage; found stage " + context.Stage + ".");
            }

            var target = context.InputParameters.Contains("Target") ? context.InputParameters["Target"] as Entity : null;
            if (target == null || !target.Contains(WorkOrder.Status))
            {
                tracing.Trace("Target does not include {0}; exiting.", WorkOrder.Status);
                return;
            }

            if (!context.PreEntityImages.Contains(PreImageAlias))
            {
                throw new InvalidPluginExecutionException(
                    "WorkOrderStatusPlugin step is missing its pre-image (alias 'PreImage'). Fix the step registration.");
            }
            var pre = context.PreEntityImages[PreImageAlias];

            var newStatus = target.GetAttributeValue<OptionSetValue>(WorkOrder.Status);
            if (newStatus == null)
            {
                throw new InvalidPluginExecutionException("A work order must always have a status.");
            }
            var oldStatus = pre.GetAttributeValue<OptionSetValue>(WorkOrder.Status);
            var from = oldStatus != null ? oldStatus.Value : WorkOrder.New;
            var to = newStatus.Value;

            if (from == to)
            {
                tracing.Trace("Status unchanged ({0}); no-op.", Label(to));
                return;
            }

            if (!IsAllowed(from, to))
            {
                throw new InvalidPluginExecutionException(
                    string.Format("A work order cannot move from {0} to {1}.", Label(from), Label(to)));
            }

            var now = context.OperationCreatedOn;
            target[WorkOrder.StatusChangedOn] = now;

            if (to == WorkOrder.InProgress && !pre.Contains(WorkOrder.ActualStart) && !target.Contains(WorkOrder.ActualStart))
            {
                target[WorkOrder.ActualStart] = now;
            }

            if (to == WorkOrder.Completed)
            {
                var notes = target.Contains(WorkOrder.ResolutionNotes)
                    ? target.GetAttributeValue<string>(WorkOrder.ResolutionNotes)
                    : pre.GetAttributeValue<string>(WorkOrder.ResolutionNotes);
                if (string.IsNullOrWhiteSpace(notes))
                {
                    throw new InvalidPluginExecutionException("Add resolution notes before completing the work order.");
                }

                target[WorkOrder.CompletedOn] = now;
                DateTime? start = target.Contains(WorkOrder.ActualStart)
                    ? target.GetAttributeValue<DateTime?>(WorkOrder.ActualStart)
                    : pre.GetAttributeValue<DateTime?>(WorkOrder.ActualStart);
                if (start.HasValue)
                {
                    target[WorkOrder.DurationMinutes] = (int)Math.Floor((now - start.Value).TotalMinutes);
                }
                else
                {
                    tracing.Trace("No actual start recorded; duration not calculated.");
                }
            }

            tracing.Trace("Transition {0} -> {1} accepted.", Label(from), Label(to));
        }

        public static bool IsAllowed(int from, int to)
        {
            if (from == to) return true;
            int[] next;
            return AllowedTransitions.TryGetValue(from, out next) && next.Contains(to);
        }

        private static string Label(int value)
        {
            string label;
            return WorkOrder.Labels.TryGetValue(value, out label) ? label : "Unknown (" + value + ")";
        }
    }
}
