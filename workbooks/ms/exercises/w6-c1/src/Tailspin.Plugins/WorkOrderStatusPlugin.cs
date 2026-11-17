using System;
using System.Collections.Generic;
using Microsoft.Xrm.Sdk;

namespace Tailspin.Plugins
{
    /// <summary>
    /// Validates work order status transitions and stamps derived columns.
    /// Intended registration: Update of contoso_workorder, PreOperation (20), Synchronous,
    /// filtering attribute contoso_status, pre-image alias "PreImage". See README.
    /// </summary>
    public class WorkOrderStatusPlugin : IPlugin
    {
        public const string PreImageAlias = "PreImage";

        /// <summary>
        /// Allowed transitions: key = current status, value = statuses it may move to.
        /// Setting a status to its current value is a no-op, not a transition.
        /// </summary>
        public static readonly IDictionary<int, int[]> AllowedTransitions = new Dictionary<int, int[]>
        {
            // TODO: fill in from the README transition table.
        };

        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));

            // TODO 1: trace the key context values (MessageName, Stage, Depth, CorrelationId).
            // TODO 2: guard the registration: wrong message/entity -> trace and return;
            //         wrong stage -> throw InvalidPluginExecutionException (see README for why).
            // TODO 3: early exit when the Target does not contain contoso_status.
            // TODO 4: read the old status from the registered pre-image (never Retrieve the row).
            //         A missing pre-image is a registration bug: throw a clear InvalidPluginExecutionException.
            // TODO 5: validate the transition; same status = no-op; illegal = user-friendly exception.
            // TODO 6: stamp derived columns on the Target (no service.Update call).

            throw new NotImplementedException("WorkOrderStatusPlugin is not implemented yet.");
        }

        /// <summary>True when moving from 'from' to 'to' is allowed (same value counts as allowed).</summary>
        public static bool IsAllowed(int from, int to)
        {
            // TODO
            throw new NotImplementedException();
        }
    }
}
