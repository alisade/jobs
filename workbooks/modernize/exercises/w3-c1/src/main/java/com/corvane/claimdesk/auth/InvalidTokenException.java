package com.corvane.claimdesk.auth;

/** The bearer token is not acceptable: bad signature, wrong issuer or audience, expired, malformed. */
public class InvalidTokenException extends RuntimeException {
    public InvalidTokenException(String message, Throwable cause) {
        super(message, cause);
    }

    public InvalidTokenException(String message) {
        super(message);
    }
}
