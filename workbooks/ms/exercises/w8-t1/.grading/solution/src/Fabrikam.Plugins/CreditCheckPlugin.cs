using System;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

namespace Fabrikam.Plugins
{
    /// <summary>
    /// Credit check for new sales orders. Registered PreValidation (10), synchronous, on Create of
    /// contoso_order: cheap to cancel there (outside the transaction, before security checks), so a
    /// declined order never opens a transaction. It must NOT write anything: work done in PreValidation of
    /// the initial operation is not rolled back when a later stage fails. The decision is handed to
    /// CreditAuditPlugin (PostOperation, inside the transaction) through shared variables.
    /// </summary>
    public class CreditCheckPlugin : IPlugin
    {
        public const string AvailableKey = "fabrikam.creditcheck.available";

        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));
            var service = ((IOrganizationServiceFactory)serviceProvider.GetService(typeof(IOrganizationServiceFactory)))
                .CreateOrganizationService(context.UserId);

            var order = (Entity)context.InputParameters["Target"];
            tracing.Trace("CreditCheckPlugin: Stage={0} Depth={1} InTransaction={2} Order={3}",
                context.Stage, context.Depth, context.IsInTransaction, order.GetAttributeValue<string>(Order.Number));

            var customerRef = order.GetAttributeValue<EntityReference>(Order.Customer);
            var amount = order.GetAttributeValue<Money>(Order.Amount);
            if (customerRef == null || amount == null)
            {
                throw new InvalidPluginExecutionException("An order needs a customer and an amount.");
            }

            var customer = service.Retrieve(Account.EntityName, customerRef.Id,
                new ColumnSet(Account.Name, Account.CreditLimit, Account.OpenBalance));
            var available = CreditMath.Available(customer);

            if (amount.Value > available)
            {
                tracing.Trace("Credit declined: amount {0:0.00}, available {1:0.00}", amount.Value, available);
                throw new InvalidPluginExecutionException(string.Format(
                    "Credit limit exceeded for {0}: available {1:0.00}, order {2:0.00}. Ask Credit Control for an override.",
                    customer.GetAttributeValue<string>(Account.Name), available, amount.Value));
            }

            context.SharedVariables[AvailableKey] = available;
            tracing.Trace("Credit approved: amount {0:0.00}, available {1:0.00}", amount.Value, available);
        }
    }

    internal static class CreditMath
    {
        public static decimal Available(Entity customer)
        {
            var limit = customer.GetAttributeValue<Money>(Account.CreditLimit);
            var open = customer.GetAttributeValue<Money>(Account.OpenBalance);
            return (limit != null ? limit.Value : 0m) - (open != null ? open.Value : 0m);
        }
    }
}
