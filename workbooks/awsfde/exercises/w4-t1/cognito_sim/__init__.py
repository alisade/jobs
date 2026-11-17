"""Local stand-ins for the Cognito user pool, the SPA and the HTTP API JWT authorizer.

Treat this as the environment, not the suspect. It follows the documented behaviour:
- LambdaConfig.PreTokenGenerationConfig.LambdaVersion picks the trigger event version.
- A V1_0 event ("version": "1") customizes the ID token only, from response.claimsOverrideDetails.
- A V2_0 event ("version": "2") customizes both tokens, from response.claimsAndScopeOverrideDetails
  (idTokenGeneration / accessTokenGeneration). Only the response fields of the configured event
  version are applied.
- V2_0 needs the Essentials or Plus feature plan (or Lite with advanced security features).
- Custom attributes the app client can read appear in the ID token, never in the access token.
- The JWT authorizer checks aud (ID token) or client_id (access token) against the app client.
Tokens are plain claim dicts: no signing, nothing here is a real token.
"""
