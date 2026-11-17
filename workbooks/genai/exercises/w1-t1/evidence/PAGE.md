# INC-20431 (Sev 3) - Assistant answers repeat words

Opened 2026-11-06 09:12 by the web storefront on-call. Escalated to you as the owner of the assistant panel.

> From #kestrel-web-support, 2026-11-06 08:47
>
> **Priya (CX lead):** Three customer complaints this morning that the shopping assistant "stutters".
> One sent a screenshot, it is in `user-screenshot.txt`. Not every answer, mostly the long ones where it
> looks things up.
>
> **Dan (web platform):** We moved the storefront to the new edge proxy tier on Tuesday night
> (CHG-8812). Nothing else changed on our side.
>
> **Mei (frontend):** I cannot reproduce it on localhost. I did see every effect run twice in dev,
> which is React StrictMode. Could prod be double-subscribing? I am tempted to ship a fix that dedupes
> renders in the component.
>
> **Priya:** Answer quality team says the model output in the gateway logs looks normal, no repeated
> words in what the model generated.

## What we know

- Started after release 2026.11.04 (web) and CHG-8812 (edge proxy), both on 2026-11-04.
- Affects maybe 3-5% of answers, nearly all longer than 15 s.
- The gateway's own transcript for the conversation in the screenshot is clean.

## Files

| File | What it is |
|---|---|
| `user-screenshot.txt` | the customer's screenshot, transcribed |
| `network-trace.txt` | HAR export from a support engineer who reproduced it on prod |
| `client-console.log` | browser console from the same session |
| `edge-proxy.log` | edge proxy access/connection log for that session |
| `gateway.log` | assistant gateway log for that session |
| `release-notes-2026.11.04.md` | web release notes |
| `CHG-8812.md` | the proxy change record |
