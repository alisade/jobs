# Current CRM inventory (exported by Tomas Ekberg, data migration lead)

## Standard objects in use
| Object | Records | Notes |
|---|---|---|
| Account | 410,000 | parent/child hierarchy up to 5 levels; record types: Customer, Partner, Prospect |
| Contact | 2,300,000 | belongs to one Account; 6% have no Account (orphans from old imports) |
| Lead | 1,100,000 | converts into Account + Contact + Opportunity; 22% converted |
| Opportunity | 640,000 | stages Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost |
| OpportunityLineItem | 1,900,000 | product, quantity, price, discount |
| OpportunityContactRole | 900,000 | contact x opportunity with a role |
| Task / Event (activities) | 48,000,000 | WhoId points at Lead or Contact, WhatId at Account, Opportunity or a custom object |
| User | 2,600 | record owner on every object; managers via a role hierarchy |

## Custom objects and fields
- `Renewal__c` (180,000): links to Opportunity and to the contract in the billing system.
- `Partner_Deal_Registration__c` (95,000): partner portal submissions; approval by a partner manager.
- 312 custom fields across objects; 41 are formula or roll-up fields (e.g. `Account.Open_Pipeline__c`
  sums open opportunity amounts; `Opportunity.Days_In_Stage__c`).
- Picklists with values that differ per record type.

## Automation (where the business logic lives)
- 23 validation rules. Examples: Closed Won requires Amount > 0 and a Close Date; Discount > 20%
  requires a manager approval record; Partner accounts require a partner tier.
- 64 flows. Examples: lead assignment round-robin by territory with manager override; stage change
  notifications to deal desk; renewal opportunity auto-created 120 days before contract end.
- 53 Apex triggers. Examples: keep `Account.Open_Pipeline__c` in sync; copy partner tier down the
  hierarchy; block deletion of accounts with open opportunities.
- Sharing rules: users see their tenant's records; partner managers see partner accounts across tenants.

## Integrations
- Marketing automation pulls new contacts every 15 minutes (cursor pagination over the CRM API).
- Billing system pushes contract end dates nightly.
- Warehouse extracts closed-won opportunities nightly.
- Partner portal writes deal registrations through the CRM API.
- Support console reads account and contact details in real time (p95 budget 150 ms).
