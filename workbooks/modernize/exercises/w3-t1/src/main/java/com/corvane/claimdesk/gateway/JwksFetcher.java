package com.corvane.claimdesk.gateway;

import java.io.IOException;

/** Fetches the issuer's JWKS document (https://corvane.okta.example/oauth2/aus1claimdesk/v1/keys in prod). */
public interface JwksFetcher {
    String fetch() throws IOException;
}
