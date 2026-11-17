# Constraints and assumptions

- Engagement: Perficient lead architect + 6 offshore engineers (Pune) + 2 nearshore (Monterrey) for
  4 months to production pilot; LFG provides a ServiceNow developer (0.5 FTE) and the Okta admin.
- Change freeze 2026-12-15 .. 2027-01-05. LFG CAB meets Tuesdays.
- AWS: LFG landing zone with Control Tower; us-east-1 primary, us-west-2 secondary; AWS Organizations SCPs
  restrict Regions to us-east-1, us-west-2.
- Vendor agents (Pune, Monterrey) keep Citrix VDI until 2027-Q3.
- No card data is handled; HR data (last 4 of SSN, date of birth) is used today for identity checks.
- Number porting from Lumen typically takes 2-4 weeks per order after LOA.
- Budget assumption: telephony + Connect usage under USD 45k/month at current volumes.
