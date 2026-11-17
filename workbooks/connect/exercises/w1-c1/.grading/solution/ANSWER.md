# ANSWER: connect/w1-c1 Harden the help desk inbound flow

## Approach

Ran `make lint` on the contractor's flow (11 errors: missing error branches, 30 s Lambda limit,
unbounded menu self-loop, attributes used before set) and rebuilt it around three rules:
nothing blocks the caller, every loop is bounded, every transfer has a working queue.

## Fix

Identify at 3 s with failure degrading to callerVerified=false; reset at 6 s with failure to the
PasswordReset queue; Loop(3) around the menu with a retry message, DoneLooping to GeneralSupport;
VIP and outage at QueuePriority 1; check staffing before transfer with overflow to GeneralSupport;
QueueAtCapacity and NoMatchingError on transfer each play a message before disconnecting; after-hours
offers 9 for outages to MajorIncident. Verified with make lint, make simulate for each path, make test.

## Trade-offs / what I would do in production

Menu and closure messages become flow modules; holidays come from hours overrides; callbacks
instead of overflow for PasswordReset; publish with versions/aliases; alarms on ContactFlowErrors.
