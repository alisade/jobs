# Recent incidents relevant to resiliency

- 2025-12-07 (Avaya era): Charlotte data center power event. Avaya ESS took over after 41 minutes because
  the failover was manual and the on-call engineer could not reach the SBC console over VPN.
- 2026-06-13: us-east-1 Lambda elevated errors for 52 minutes in one AZ group. Connect itself was healthy,
  but lfg-identify-caller timed out at 8 s for 30% of calls; the IVR stalled before the menu (fixed in w1-c1).
- 2026-08-29: Okta degraded 20 minutes; agents already logged in kept working, new logins failed.
