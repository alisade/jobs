using System;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

namespace Fabrikam.Plugins
{
    /// <summary>
    /// Credit check for new sales orders (release 2.7, 2026-09-22).
    /// Rejects an order when it exceeds the customer's available credit and writes the
    /// decision to contoso_creditaudit, which Finance reconciles against orders every morning.
    /// </summary>
    public class CreditCheckPlugin : IPlugin
    {
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
            var limit = customer.GetAttributeValue<Money>(Account.CreditLimit);
            var open = customer.GetAttributeValue<Money>(Account.OpenBalance);
            var available = (limit != null ? limit.Value : 0m) - (open != null ? open.Value : 0m);
            var approved = amount.Value <= available;

            var audit = new Entity(CreditAudit.EntityName);
            audit[CreditAudit.Name] = "Credit check " + order.GetAttributeValue<string>(Order.Number);
            audit[CreditAudit.OrderNumber] = order.GetAttributeValue<string>(Order.Number);
            audit[CreditAudit.Customer] = customerRef;
            audit[CreditAudit.Amount] = amount;
            audit[CreditAudit.Available] = new Money(available);
            audit[CreditAudit.Decision] = approved ? "Approved" : "Declined";
            audit[CreditAudit.CheckedOn] = context.OperationCreatedOn;
            var auditId = service.Create(audit);
            tracing.Trace("Credit {0}: amount {1:0.00}, available {2:0.00}, audit {3}",
                approved ? "approved" : "declined", amount.Value, available, auditId);

            if (!approved)
            {
                throw new InvalidPluginExecutionException(string.Format(
                    "Credit limit exceeded for {0}: available {1:0.00}, order {2:0.00}. Ask Credit Control for an override.",
                    customer.GetAttributeValue<string>(Account.Name), available, amount.Value));
            }
        }
    }
}
