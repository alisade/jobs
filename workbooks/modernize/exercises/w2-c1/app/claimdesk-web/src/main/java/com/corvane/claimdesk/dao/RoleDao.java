package com.corvane.claimdesk.dao;

import java.io.IOException;
import java.io.InputStream;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HashSet;
import java.util.Properties;
import java.util.Set;

import javax.annotation.Resource;
import javax.enterprise.context.ApplicationScoped;
import javax.sql.DataSource;

/** Fine-grained application roles that never made it into LDAP. */
@ApplicationScoped
public class RoleDao {

    @Resource(lookup = "java:/jdbc/ClaimDeskDS")
    private DataSource ds;

    private final Properties queries = new Properties();

    public RoleDao() {
        try (InputStream in = RoleDao.class.getResourceAsStream("/queries.properties")) {
            queries.load(in);
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }
    }

    public Set<String> rolesFor(String uid) {
        Set<String> out = new HashSet<>();
        try (Connection c = ds.getConnection(); PreparedStatement ps = c.prepareStatement(queries.getProperty("role.byUser"))) {
            ps.setString(1, uid);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    out.add(rs.getString(1));
                }
            }
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
        return out;
    }
}
