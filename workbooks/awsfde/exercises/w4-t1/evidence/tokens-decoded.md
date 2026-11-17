# Decoded tokens captured by Brightline IT on 2026-11-12 (FAKE examples for this exercise)

These are claim sets only: not real tokens, no signatures. User okafor@brightline.example.

## ID token (payload)

```json
{
  "sub": "b2e1d3c5-0003-4b2f-8d22-brgt00000003",
  "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TideW8ter",
  "aud": "5tw8askspa0client0id00000",
  "token_use": "id",
  "cognito:username": "brightline-saml_okafor@brightline.example",
  "email": "okafor@brightline.example",
  "custom:tenant_id": "brightline-health",
  "tenant_id": "brightline-health",
  "identities": [{"providerName": "brightline-saml", "providerType": "SAML", "primary": "true"}]
}
```

## Access token (payload)

```json
{
  "sub": "b2e1d3c5-0003-4b2f-8d22-brgt00000003",
  "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TideW8ter",
  "client_id": "5tw8askspa0client0id00000",
  "token_use": "access",
  "scope": "openid email ask/shipments.read",
  "username": "brightline-saml_okafor@brightline.example"
}
```
