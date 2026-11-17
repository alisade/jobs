# Escalation CX-8812: assistant is offering a promo code that does not exist

**Opened:** 2026-11-10 09:20 PT by customer-care lead  **Assigned:** you (assistant on call)  **Sev:** 2

> Since Saturday evening customers have been chatting with us angry that the website assistant told them
> code SPRING20 takes 20 percent off the Ridgeline 2P tent and "today it is $199.20". Checkout rejects the
> code. 37 contacts so far, two customers posted screenshots on social media, and three stores honored the
> price at the register to calm people down. Legal asks whether we are obliged to honor what the bot said.
> Some customers also mention a "FREESHIP50" code for sleeping bags.

## Thread

**09:31 assistant-pm:** we upgraded the model version on Saturday too (release notes). I bet the new model
hallucinates more. Can we roll the model back?

**09:36 ml-eng:** the grounding check is supposed to block invented prices and codes. grounding.log shows
`grounded=True` for these answers, so the check thinks SPRING20 is in the tool results??

**09:44 merchandising:** there is no SPRING20 promotion and there never was. FALL20 existed for the tent
but expired on Oct 31.

**09:52 trust-and-safety:** the review moderation queue auto-approves on-topic reviews. We do not read them
before they go live.

Find the root cause, show it from the evidence, and fix it so this cannot happen again with the next
review someone writes. Do not just block the string SPRING20.
