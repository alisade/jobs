package com.corvane.claimdesk.dao;

import java.math.BigDecimal;
import java.sql.CallableStatement;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;

import javax.annotation.Resource;
import javax.enterprise.context.ApplicationScoped;
import javax.sql.DataSource;

@ApplicationScoped
public class ReserveDao {

    @Resource(lookup = "java:/jdbc/ClaimDeskDS")
    private DataSource ds;

    public void release(String claimNumber, BigDecimal amount) {
        try (Connection c = ds.getConnection()) {
            try (PreparedStatement ps = c.prepareStatement(
                    "UPDATE RESERVE_LINE SET OUTSTANDING = OUTSTANDING - ? WHERE CLAIM_NUMBER = ? AND LINE_TYPE = 'INDEMNITY'")) {
                ps.setBigDecimal(1, amount);
                ps.setString(2, claimNumber);
                ps.executeUpdate();
            }
            try (CallableStatement cs = c.prepareCall("{call PKG_RESERVE.RECALC(?)}")) {
                cs.setString(1, claimNumber);
                cs.execute();
            }
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }
}
