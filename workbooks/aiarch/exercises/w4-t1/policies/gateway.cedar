// Lighthouse tools gateway: Cedar policy set (Policy in AgentCore, simplified model).
// Principal: User built from the verified JWT claims (role, username, team when the IdP sends it).
// Actions: one per gateway tool. context.input holds the tool call arguments.
// Policies are numbered policy0, policy1, ... in file order; the decision log uses those ids.

// policy0: employees file access requests for themselves only
permit(principal, action == Action::"create_access_request", resource)
when { principal.role == "employee" && context.input.user == principal.username };

// policy1: managers approve access requests
permit(principal, action == Action::"approve_access_request", resource)
when { principal.role == "manager" };

// policy2: never approve outside your own team
forbid(principal, action == Action::"approve_access_request", resource)
unless { principal.team == context.input.team };

// policy3: never approve your own request
forbid(principal, action == Action::"approve_access_request", resource)
when { context.input.requester == principal.username };

// policy4: auditors and managers may read
permit(principal, action in [Action::"get_access_request", Action::"list_access_requests"], resource)
when { principal.role == "auditor" || principal.role == "manager" };
