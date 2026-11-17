package com.corvane.claimdesk.notes;

import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.sql.DataSource;

/** Production wiring: the datasource comes from JNDI (java:/jdbc/ClaimDeskDS on the app server). */
public final class JdbcSupport {

    private JdbcSupport() {
    }

    public static DataSource lookup(String jndiName) throws NamingException {
        return (DataSource) new InitialContext().lookup(jndiName);
    }
}
