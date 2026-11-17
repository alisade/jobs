package com.corvane.claimdesk.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import javax.annotation.Resource;
import javax.enterprise.context.ApplicationScoped;
import javax.sql.DataSource;

import com.corvane.claimdesk.model.Claim;

@ApplicationScoped
public class ClaimDao {

    @Resource(lookup = "java:/jdbc/ClaimDeskDS")
    private DataSource ds;

    private static final String ARCHIVE_SCHEMA = "CLMARCH";

    public Claim findByNumber(String number) {
        String sql = "SELECT CLAIM_ID, CLAIM_NUMBER, POLICY_NUMBER, STATUS, NVL(ADJUSTER_ID, 0) FROM CLAIM WHERE CLAIM_NUMBER = ?";
        return query(sql, number);
    }

    /** Archived claims live in one table per year: CLMARCH.CLAIM_ARCHIVE_2019, _2020, ... */
    public Claim findArchived(String number, int year) {
        String sql = "SELECT CLAIM_ID, CLAIM_NUMBER, POLICY_NUMBER, STATUS, 0 FROM " + ARCHIVE_SCHEMA + ".CLAIM_ARCHIVE_" + year
                + " WHERE CLAIM_NUMBER = ? AND ROWNUM = 1";
        return query(sql, number);
    }

    public void addNote(String number, String author, String text) {
        String sql = "INSERT INTO CLAIM_NOTE (NOTE_ID, CLAIM_NUMBER, AUTHOR, NOTE_TEXT, CREATED) VALUES (SEQ_NOTE.NEXTVAL, ?, ?, ?, SYSDATE)";
        try (Connection c = ds.getConnection(); PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, number);
            ps.setString(2, author);
            ps.setString(3, text);
            ps.executeUpdate();
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    private Claim query(String sql, String number) {
        try (Connection c = ds.getConnection(); PreparedStatement ps = c.prepareStatement(sql)) {
            ps.setString(1, number);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? new Claim(rs.getLong(1), rs.getString(2), rs.getString(3), rs.getString(4), rs.getLong(5)) : null;
            }
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }
}
