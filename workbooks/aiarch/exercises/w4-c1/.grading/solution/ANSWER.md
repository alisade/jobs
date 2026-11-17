# ANSWER: aiarch/w4-c1

## Approach

One decode helper (RS256 only, kid lookup, issuer and audience, exp/nbf with the injected clock)
used for both the inbound and the exchanged token; the exchange form built per RFC 8693; every
property of the issued token checked before it is cached or used.

## Fix

Token path: (1) the IdP issues the manager's access token: iss idp, aud lighthouse-gateway,
sub lwong, scope includes access.request.write. (2) Runtime or Gateway validates it inbound.
(3) The tool exchanges it: subject_token = that token, actor_token = the agent's token
(sub lighthouse-agent), audience https://access.harborpoint.example, scope narrowed to
access.request.write. (4) The IdP returns aud = the API, sub = lwong, act.sub = lighthouse-agent,
300 s lifetime. (5) The API validates its own audience and authorizes lwong. The original token
replayed at the API fails on audience. Verified with make test.

## Trade-offs / what I would do in production

- On AgentCore: the agent has a workload identity; `GetWorkloadAccessTokenForJWT` binds the
  user's JWT to it; an OAuth2 credential provider in TOKEN_EXCHANGE mode holds the client
  credentials; `GetResourceOauth2Token` with ON_BEHALF_OF_TOKEN_EXCHANGE returns the downstream
  token. The agent code never sees a client secret.
- Entra ID implements OBO with the RFC 7523 JWT-bearer grant, not RFC 8693; confirm the IdP
  before designing.
- Short-lived exchanged tokens limit revocation lag; cache per user and scope, never across
  users. Refresh JWKS on unknown kid with a rate limit.
