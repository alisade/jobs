# Reference: connect/w1-c1

The reference flow is `.grading/solution/flows/helpdesk-inbound.json`. Shape:

```
start-logging -> check-hours --True--> identify-caller(3s) --ok--> set-verified --> check-vip
                    |                        |error            |error
                    |False                   v                 v
                    v                   set-unverified ------> check-vip
              after-hours-msg -> after-hours-outage --9--> set-q-major
                                       |other/timeout -> disconnect
check-vip --true--> set-q-vip -> vip-priority(1) -> check-staffing
          --else--> menu-loop(3) --Continue--> main-menu --1--> password-reset(6s) -> check-reset
                         |Done                    |2 -> set-q-general        |SENT -> reset-sent-msg -> disconnect
                         v                        |3 -> set-q-major -> major-priority(1)
                    set-q-general                 |timeout/invalid -> menu-retry-msg -> menu-loop
check-staffing --staffed>0--> transfer --QueueAtCapacity--> at-capacity-msg -> disconnect
               --false------> overflow-msg -> set-q-overflow(General) -> transfer
```

Key points an interviewer looks for:

- The identify Lambda budget is small because the caller hears dead air while it runs and
  Connect retries a failed synchronous invoke within the same 8 s budget; failure degrades
  to "unverified" instead of blocking. Slow work (ticket lookups, LLM calls) belongs in
  async mode (up to 60 s, Wait + Load Lambda result) or after the transfer.
- Retry loops must be bounded with the Loop block; Connect does not stop an unbounded
  menu loop for you, and a no-input caller would loop until they hang up.
- `$.External` holds only the most recent Lambda result and is not saved to the contact
  record: copy what you need into contact attributes immediately.
- Queue priority on the working queue (`UpdateContactRoutingBehavior`) is how VIP and outage
  calls jump the line; routing profile priority/delay only decides between queues for an agent.
- Check staffing (`CheckMetricData` NumberOfAgentsStaffed, only `NumberGreaterThan 0` is
  allowed for agent counts) prevents parking callers in a queue nobody is logged in to.
- In production: put the menu and the closed/capacity messages in flow modules, publish
  with versions/aliases, alarm on `ContactFlowErrors`/`ContactFlowFatalErrors`, and keep
  holiday closures in a data store the flow reads rather than hard-coding them.
