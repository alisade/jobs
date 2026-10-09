using System;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

namespace Fabrikam.Plugins
{
    /// <summary>
    /// Writes the credit-exposure ledger row. Registered PostOperation (40), synchronous, on Create of
    /// contoso_order: it runs inside the same database transaction as the order, so if any step fails the
    /// order and the ledger row roll back together, and it can link to the new order id.
    /// </summary>
    public class CreditAuditPlugin : IPlugin
    {
        public void Execute(IServiceProvider serviceProvider)
        {
            var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            var tracing = (ITracingService)serviceProvider.GetService(typeof(ITracingService));
            var service = ((IOrganizationServiceFactory)serviceProvider.GetService(typeof(IOrganizationServiceFactory)))
                .CreateOrganizationService(context.UserId);

            if (context.Stage != 40 || context.MessageName != "Create")
            {
                throw new InvalidPluginExecutionException("CreditAuditPlugin must be registered on PostOperation (40) of Create.");
            }

            var order = (Entity)context.InputParameters["Target"];
            var orderId = context.OutputParameters.Contains("id") ? (Guid)context.OutputParameters["id"] : order.Id;
            var customerRef = order.GetAttributeValue<EntityReference>(Order.Customer);
            var amount = order.GetAttributeValue<Money>(Order.Amount);

            // PreValidation shared variables are on ParentContext for Create (Learn: shared variables).
            decimal available;
            var parent = context.ParentContext;
            if (parent != null && parent.SharedVariables.Contains(CreditCheckPlugin.AvailableKey))
            {
                available = (decimal)parent.SharedVariables[CreditCheckPlugin.AvailableKey];
            }
            else if (context.SharedVariables.Contains(CreditCheckPlugin.AvailableKey))
            {
                available = (decimal)context.SharedVariables[CreditCheckPlugin.AvailableKey];
            }
            else
            {
                tracing.Trace("No shared credit decision found; recomputing.");
                var customer = service.Retrieve(Account.EntityName, customerRef.Id, new ColumnSet(Account.CreditLimit, Account.OpenBalance));
                available = CreditMath.Available(customer);
            }

            var audit = new Entity(CreditAudit.EntityName);
            audit[CreditAudit.Name] = "Credit check " + order.GetAttributeValue<string>(Order.Number);
            audit[CreditAudit.OrderNumber] = order.GetAttributeValue<string>(Order.Number);
            audit[CreditAudit.OrderId] = new EntityReference(Order.EntityName, orderId);
            audit[CreditAudit.Customer] = customerRef;
            audit[CreditAudit.Amount] = amount;
            audit[CreditAudit.Available] = new Money(available);
            audit[CreditAudit.Decision] = "Approved";
            audit[CreditAudit.CheckedOn] = context.OperationCreatedOn;
            var id = service.Create(audit);
            tracing.Trace("CreditAuditPlugin: Stage={0} InTransaction={1} ledger row {2} for order {3}", context.Stage, context.IsInTransaction, id, orderId);
        }
    }
}
