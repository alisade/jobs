# aiarch/w4-c1 - On-behalf-of token exchange for Lighthouse tools

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 4 (Mon: OAuth 2.0 and JWT; Tue: OBO and RFC 8693; Wed: AgentCore Identity)

## Scenario

A Harbor Point manager asks the Lighthouse agent to file an access request. The agent's tool
calls the access-requests API. Today the tool forwards the manager's own token, issued for
`lighthouse-gateway`, and the API rejects it on audience. The proposed quick fix, a service
account for the agent, was rejected by security: the API would see the agent and not the
manager, and its own authorization ("managers request access only for their team") would stop
working. That is the confused-deputy problem.

The design is OAuth on-behalf-of with RFC 8693 token exchange: the tool exchanges the user's
token at the IdP for a new token whose audience is the API, whose subject is still the user,
whose `act` claim names the agent, and whose scope is no wider than both what the user has and
what the tool needs. On AgentCore this is what an OAuth2 credential provider in
`TOKEN_EXCHANGE` mode does for you; here you build the client logic yourself so you can
explain every check.

`obo/fakeidp.py` is an offline IdP that signs tokens and answers token-exchange requests (and
can be told to misbehave). `obo/api.py` is the API's token check. Both work as shipped.

## Requirements (`obo/exchange.py`)

1. `validate_inbound(token, jwks, issuer, audience, now)`: RS256 only (reject `none`, HS256
   and anything else), key chosen by `kid` from the JWKS, issuer and audience checked,
   `exp`, `iss`, `aud`, `sub` required, `exp`/`nbf` checked against `now` with 60 s leeway.
   Raise `TokenError` with a clear reason.
2. `build_exchange_request(...)`: the RFC 8693 form: `grant_type`
   `urn:ietf:params:oauth:grant-type:token-exchange`, `subject_token` and
   `subject_token_type` access_token, `requested_token_type` access_token, `audience`,
   optional `resource`, space-separated `scope`, and `actor_token` with `actor_token_type`
   jwt only when an actor token is given.
3. `OboClient.get_downstream_token(inbound_token, target)`:
   - validates the inbound token (audience `lighthouse-gateway`) using the injected clock;
   - requests the intersection of the user's scopes and the target's scopes; none left raises
     `InsufficientScope` without calling the IdP;
   - sends the actor token when configured;
   - checks the response: an access token was issued, `issued_token_type` is access_token,
     it is not the inbound token, it validates for the target audience, `sub` is the user,
     no scope beyond what was requested, `act.sub` is the agent when `agent_client_id` is set;
   - caches per (user, target, scopes) and refreshes 60 s before `exp`;
   - unknown targets and IdP errors raise `TokenError` (include the IdP's `error`).
4. Never forward the inbound token.

## Acceptance criteria (what the grader checks)

- The visible proof: the API sees the user with the agent as actor, and the user's original
  token replayed at the API fails on audience.
- Hidden tests: request shape, scope narrowing, a misbehaving IdP (wrong audience, wrong
  subject, extra scope), actor requirement, cache hits, refresh and per-user isolation, and
  rejection of expired, wrong-audience, HS256, foreign-key and unknown-kid tokens.
- `ANSWER.md`: the full token path for one request (every token, issuer, audience, subject),
  and how this maps onto AgentCore Identity (workload identity, `GetWorkloadAccessTokenForJWT`,
  OAuth2 credential provider, `GetResourceOauth2Token`).

## How to run

```bash
make setup     # builds aiarch/.venv once
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w4-c1
make clean
```

## What to submit

`obo/exchange.py` and `ANSWER.md`.
