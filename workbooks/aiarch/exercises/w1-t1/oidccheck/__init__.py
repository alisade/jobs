"""oidccheck: evaluate an IAM role trust policy against a decoded GitLab id_token (offline).

Models what STS does for AssumeRoleWithWebIdentity: the statement must Allow
sts:AssumeRoleWithWebIdentity for the Federated principal that matches the token issuer, and
every condition must hold. Condition keys are "<provider>:<claim>", e.g. gitlab.com:sub and
gitlab.com:aud. Operators: StringEquals, StringLike, StringNotEquals, StringNotLike, with
ForAnyValue:/ForAllValues: not needed here. IAM only exposes aud and sub (and amr where the
provider sends it) as condition keys for OIDC providers; other claims in the token are not
usable in a trust policy, so this tool ignores them on purpose.
"""
from .engine import check  # noqa: F401
