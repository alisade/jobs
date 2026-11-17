# Volumes, systems and constraints (fictional)

| Item | Value |
|---|---|
| Controls in scope for ControlPilot in FY2026 | 6 ITGCs (CM-03 program change, CM-05 emergency change, AC-02 access provisioning, AC-04 terminations, AC-07 quarterly user access review, OP-01 batch job monitoring) |
| Samples per year | about 25 per daily/multiple-daily control per test period, 2 interim + 1 roll-forward period; about 600 sample items a year |
| Evidence per item | 3-12 files: ticket exports, PR JSON, CI logs, deploy logs, approval e-mails (PDF), screenshots, Excel extracts |
| Model calls per item | 8-20 (extraction, retrieval, tool calls), about 40k input tokens and 3k output tokens per item |
| Systems | GitHub Enterprise Cloud, ServiceDesk (change tickets), GRC Hub (issues, workpapers), Entra ID, Azure DevOps pipelines, SAP (for later controls) |
| Cloud | Azure is the MFH standard (subscriptions per environment, hub-and-spoke VNets). Google Cloud is approved only for the Gemini models under the enterprise agreement |
| Model | Gemini through Gemini Enterprise Agent Platform (formerly Vertex AI), us-central1 or another US region |
| Team | 3 engineers, 1 audit data analyst, IT audit seniors as reviewers |
| Peak | year-end roll-forward: 150 items in 10 business days |
