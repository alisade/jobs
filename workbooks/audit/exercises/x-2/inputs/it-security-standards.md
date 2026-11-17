# MFH IT security standards that apply (extract, fictional)

- SEC-02 Identity: workloads authenticate with managed identities or federated identities. Service
  account keys, client secrets in app settings and personal access tokens are prohibited.
- SEC-05 Network: production workloads run in a VNet; storage and key vaults use private endpoints;
  outbound internet goes through the egress firewall with an allow list of FQDNs.
- SEC-07 Logging: security-relevant events go to the central SIEM (Microsoft Sentinel) within 5
  minutes; application audit logs are retained 7 years in immutable storage.
- SEC-09 Third-party AI: a vendor model may process confidential data only under an enterprise
  agreement with no training on customer data, a US data-residency commitment and logging of
  prompts and responses by MFH.
- SEC-11 Least privilege: write access to systems of record (GRC, ticketing, source control) needs
  an approval step for automated actors; read access is scoped to the engagement.
