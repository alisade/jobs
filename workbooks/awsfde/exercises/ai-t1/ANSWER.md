# ANSWER: awsfde/ai-t1 Weekly summary sent to an outside address

## Approach

<!-- What you checked first and what each step ruled out. -->

## Root cause

<!-- The document, the instruction in it, how it was ingested; the tool and the loop that let the
model's choice become an email. Evidence: agent.log lines (retrieval doc ids, share_report args),
the audit CSV, the replay with the previous guardrail version. -->

## Fix

<!-- What the server now enforces, and how you verified it. Why wrapping retrieved text is not the control. -->

## Trade-offs / what I would do in production

<!-- Exposure statement for Corvid (what data, to whom, when); remove the document; product
changes: partner uploads, write tools behind confirmation, egress allowlists, alarms on refused
recipients, injection cases in the eval suite. -->
