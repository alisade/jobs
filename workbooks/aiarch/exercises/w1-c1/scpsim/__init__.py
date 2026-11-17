"""scpsim: a small offline evaluator for AWS Organizations SCPs and RCPs.

It models the parts of policy evaluation that matter for guardrail design. It is not a full
IAM engine (no identity policies, no permissions boundaries, no session policies):

- Policies attach to the root, OUs and accounts. A request is evaluated against every policy
  on the path from the root to the account (root -> OU -> nested OU -> account).
- SCPs: at EVERY level on that path at least one attached SCP must Allow the action
  (FullAWSAccess does this), and no attached SCP may Deny it. Explicit deny wins.
- RCPs: same path rule, but an RCP is evaluated against the RESOURCE's account, and
  RCPFullAWSAccess is implicit (AWS manages it; you cannot detach it), so only Deny matters.
- SCPs do not apply to the management account or to service-linked roles. RCPs do not apply
  to resources in the management account, or to requests made by service-linked roles.
- Action / NotAction, Resource / NotResource with * and ? wildcards (actions are
  case-insensitive, resources case-sensitive).
- Condition operators: String(Not)Equals, String(Not)Like, StringEqualsIgnoreCase,
  Arn(Not)Equals, Arn(Not)Like, Bool, Null, Numeric*, each optionally with IfExists, and the
  ForAnyValue: / ForAllValues: set prefixes. Multiple operators and keys are ANDed, multiple
  values for one key are ORed (negated operators: none of the values may match).
- Missing condition keys follow IAM: a positive operator is false, a negated operator
  (StringNotEquals, StringNotLike, ArnNotEquals, ArnNotLike, NumericNotEquals) is true,
  ...IfExists is true, Null tests presence, ForAllValues is true, ForAnyValue is false.

Use it from tests or from the CLI (python -m scpsim requests.json).
"""

from .engine import Decision, Org, evaluate, load_org, load_policy, policy_size

__all__ = ["Decision", "Org", "evaluate", "load_org", "load_policy", "policy_size"]
