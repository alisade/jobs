package com.corvane.claimdesk.auth;

import com.unboundid.ldap.listener.InMemoryDirectoryServer;
import com.unboundid.ldap.listener.InMemoryDirectoryServerConfig;

/** An embedded LDAP server loaded with the corvane.ldif snapshot of the production directory. */
final class Directory {

    private Directory() {
    }

    static InMemoryDirectoryServer start() throws Exception {
        InMemoryDirectoryServerConfig cfg = new InMemoryDirectoryServerConfig("dc=corvane,dc=local");
        cfg.setSchema(null); // the snapshot carries a custom accountStatus attribute
        InMemoryDirectoryServer ds = new InMemoryDirectoryServer(cfg);
        ds.importFromLDIF(true, Directory.class.getResource("/corvane.ldif").getPath());
        ds.startListening();
        return ds;
    }
}
