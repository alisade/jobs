# Role 6: Senior Staff Platform Engineer (GCP, Terraform): highlights

The posting is in [posting.md](posting.md). The full material list with links is in [details.md](details.md).

This track is different from the other roles. It is a platform role, not an AI role. AI appears once, as
"Eliminate toil through the automation of existing processes with modern tooling including AI tools and
agentic workflows". So most of this track is GCP, GKE, Terraform and Crossplane, and only the last section
is about agents.

From the shared core you only need [section 1](../../shared/details.md#1-agentic-coding-tools-as-an-engineering-platform)
(Claude Code as a platform), [section 4](../../shared/details.md#4-mcp-model-context-protocol) (MCP),
[section 5](../../shared/details.md#5-verification-and-evals) (verification) and
[section 6](../../shared/details.md#6-llm-security) (LLM security). Skip the rest for this role.

## Where you start

This is the closest fit to your background of all the roles you are applying to. The core of the job is
what you have done for 26 years: IaC, Kubernetes fleets, CI/CD, security controls, incidents and on-call.
The gap is the cloud brand, not the discipline.

| Posting asks for | You already have |
|---|---|
| IaC with Terraform, Crossplane and Helm charts ("a must-have") | Terraform through Spacelift (stacks, policies, approval gates), CDK in TypeScript, CloudFormation, Helm charts you author and release. Crossplane: no |
| Zero downtime maintenance for fleets of Kubernetes clusters | EKS fleets with Karpenter and access entries, ArgoCD Application CRs and chart releases across clusters |
| CI/CD with Jenkins or ArgoCD | Both, in production: Jenkins pipelines and pod templates, ArgoCD Application CRs and chart release pipelines, GitHub Actions |
| Declarative tools "such as Terraform, Crossplane, or Cloud Formation" | Terraform and CloudFormation, daily |
| Security controls in DevOps processes, DevSecOps | Least-privilege IAM, EKS access entries, pre-push policy hooks, approval gates, backup before every live mutation |
| Exceptional troubleshooting, first line of architectural authority | 26 years of P1s across AWS, Azure, Kubernetes, Jenkins, AD, Linux and Windows |
| 12 hour on-call rotation | You have done on-call for years |
| Monitoring: Prometheus, Grafana, OpenTelemetry (preferred) | CloudWatch and New Relic. Prometheus/Grafana/OTel hands-on is thinner |
| Go, Python or Bash | Bash and Python for ops, TypeScript for CDK. Go: no |
| Eliminate toil with AI tools and agentic workflows | A daily Claude Code harness with skills, hooks and MCP servers (Jira, Spacelift, AWS) that automates real ops work |
| GCP or Alibaba, and "migration experience from cloud to Terraform" | Not yet. This is the main gap |

## Honest fit note

- **The hard filter is GCP.** The header says "Need GCP or Alibaba" and "We do not need AWS or Azure
  experience". A recruiter screen may reject an AWS/Azure resume on keywords alone. You cannot fix that
  with wording. You fix it with GCP work you can point at: a public repo and, ideally, a Google Cloud
  certification.
- **The posting contradicts itself.** The header says AWS/Azure are not needed and GCP or Alibaba is
  required. The qualifications list says "Experience with cloud platforms such as AWS, Azure, or Google
  Cloud Platform" and "Terraform, Crossplane, or Cloud Formation". Also "minimum 10 years" in the header
  against "3 to 10 years" in the qualifications. Ask the recruiter directly: "Is GCP production experience
  a hard requirement, or is strong Terraform/Kubernetes on another cloud plus hands-on GCP acceptable?"
  and "Which cloud does the MDM/RIQ/RDM platform run on today, GCP or Alibaba?"
- **How to present AWS/Azure honestly.** Do not hide it and do not lead with it. Lead with the
  cloud-neutral parts that are the actual job: Terraform at scale, Kubernetes fleet operations, ArgoCD and
  Helm, policy and approval gates, incident leadership. Then show GCP as a deliberate move: "I mapped my
  AWS patterns onto GCP and built this", with the repo link. Say plainly that your production GCP time is
  limited. Senior interviewers respect that more than inflated claims, and the concepts map closely
  (accounts to projects, OUs to folders, SCPs to org policies, IRSA/Pod Identity to Workload Identity,
  EKS to GKE, CloudWatch to Cloud Monitoring).
- **"Migration from cloud to Terraform"** most likely means taking resources that were created by hand or
  by other tools and bringing them under Terraform. You know Terraform state well from Spacelift-managed
  stacks, but bulk import across many projects is not on your record. Treat it as a gap until you have
  done it on GCP and can show the result.

## Gaps, most important first

1. **GCP foundations in depth.** Resource hierarchy, IAM and service accounts, Workload Identity
   Federation, Shared VPC, org policies, VPC Service Controls. This is the screening filter.
2. **GKE fleet operations.** Release channels, maintenance windows and exclusions, surge vs blue-green
   node pool upgrades, GKE fleets. Kubernetes transfers; the GKE knobs do not.
3. **Bringing existing GCP resources under Terraform.** Import blocks, `terraform plan -generate-config-out`,
   `gcloud beta resource-config bulk-export`, and doing it safely across many projects.
4. **Crossplane.** Named as a must-have IaC tool. You have never run it.
5. **GCP DevSecOps services.** Binary Authorization, Artifact Registry and Artifact Analysis scanning,
   Security Command Center, Secret Manager.
6. **Prometheus, Grafana, OpenTelemetry**, and Google Cloud Managed Service for Prometheus.
7. **Go**, enough to read and write small platform tools and read provider/operator code.
8. **Alibaba Cloud.** Only if the recruiter says the platform runs there. Otherwise ignore it.

## Six-week plan

| Week | Focus | Output |
|---|---|---|
| 1 | GCP fundamentals mapped from AWS: hierarchy, IAM, service accounts, WIF, Shared VPC, org policies. Start the free trial and set up an organization | Terraform for org, folders, projects, Shared VPC and org policies, applied from GitHub Actions with WIF (no keys) |
| 2 | GKE: two clusters registered to a fleet, release channels, maintenance windows, surge and blue-green upgrades, PDBs | A written zero-downtime upgrade runbook and a script that does a blue-green node pool upgrade |
| 3 | Bringing existing resources under Terraform: click-ops some resources, then import them with import blocks, generated config and bulk-export | A "migration" directory that shows before/after and a clean `terraform plan` with no changes |
| 4 | Crossplane with the GCP provider family, ArgoCD app-of-apps with Helm | A namespaced "app database" XR that a developer can request from Git |
| 5 | DevSecOps and observability: Binary Authorization, Artifact Registry scanning, Secret Manager, Managed Prometheus, Grafana, OTel Collector | Signed-image-only admission on one cluster, an SLO dashboard and burn-rate alert |
| 6 | Go basics, then the agentic toil workflow; book the certification exam | A small Go CLI, and the import-drafting agent with a human approval gate |

Book either the Professional Cloud DevOps Engineer or the Professional Cloud Architect exam in week 1 so
the date drives the study (see [details section 12](details.md#12-certification-and-how-to-present-the-background)).
DevOps Engineer is closer to this role.

## Portfolio project: a GCP platform repo

One public repo, built on the free trial, that shows every must-have in the posting:

- **Foundation in Terraform:** organization, folders (platform, workloads), projects, Shared VPC, org
  policies, remote state in GCS, CI applies through Workload Identity Federation.
- **Fleet:** two GKE clusters (for example "blue" and "green" regions or tiers) registered to one fleet,
  on a release channel with maintenance windows.
- **GitOps:** ArgoCD app-of-apps that installs Helm charts on both clusters through an ApplicationSet.
- **Self-service:** Crossplane with the GCP provider; a namespaced `AppDatabase` XR that creates a Cloud
  SQL instance, database, user and a secret.
- **Zero-downtime maintenance:** a runbook plus a script that does a blue-green node pool upgrade and
  proves no requests failed (a load generator running during the upgrade, with the error count in the README).
- **Migration:** a set of resources created by hand, then brought under Terraform with import blocks and
  generated config, ending in a no-op plan.
- **Agentic toil workflow:** an agent that inventories unmanaged resources through Cloud Asset Inventory,
  diffs them against Terraform state, drafts import blocks and config, runs `terraform plan`, and stops
  for a human to approve. It never applies.

Keep costs down: small machine types, zonal clusters, and a `make destroy` you run at the end of each
session. Do not include any GSA or Lakeview specifics.

## One-line pitch

"I have run Terraform, Kubernetes fleets and GitOps in production for years on AWS and Azure; I have
rebuilt those patterns on GCP in a public repo, and I use agent workflows to remove toil without giving
up approval gates or a clean plan."
