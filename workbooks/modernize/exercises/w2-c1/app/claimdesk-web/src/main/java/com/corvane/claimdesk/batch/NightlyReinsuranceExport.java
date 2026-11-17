package com.corvane.claimdesk.batch;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Properties;

import javax.annotation.Resource;
import javax.ejb.Schedule;
import javax.ejb.Singleton;
import javax.sql.DataSource;

import com.corvane.claimdesk.web.StartupListener;
import com.jcraft.jsch.ChannelSftp;
import com.jcraft.jsch.JSch;
import com.jcraft.jsch.Session;

/** Writes the Halberd Re bordereau and pushes it over SFTP. Runs inside the app server. */
@Singleton
public class NightlyReinsuranceExport {

    @Resource(lookup = "java:/jdbc/ClaimDeskDS")
    private DataSource ds;

    @Schedule(hour = "2", minute = "0", persistent = false)
    public void run() throws Exception {
        Path outbox = Paths.get(StartupListener.CONFIG.getProperty("outbox.dir", "/var/claimdesk/outbox"));
        Path file = outbox.resolve("bordereau-" + java.time.LocalDate.now() + ".csv");
        StringBuilder csv = new StringBuilder("claim,policy,outstanding,adjuster\n");
        try (Connection c = ds.getConnection();
             PreparedStatement ps = c.prepareStatement(
                     "SELECT c.CLAIM_NUMBER, c.POLICY_NUMBER, SUM(r.OUTSTANDING), c.ADJUSTER_ID FROM CLAIM c "
                             + "JOIN RESERVE_LINE r ON r.CLAIM_NUMBER = c.CLAIM_NUMBER WHERE c.REINSURED = 'Y' "
                             + "GROUP BY c.CLAIM_NUMBER, c.POLICY_NUMBER, c.ADJUSTER_ID");
             PreparedStatement names = c.prepareStatement(queries().getProperty("adjuster.byRegion"));
             ResultSet rs = ps.executeQuery()) {
            names.setString(1, "ALL");
            while (rs.next()) {
                csv.append(rs.getString(1)).append(',').append(rs.getString(2)).append(',')
                        .append(rs.getBigDecimal(3)).append(',').append(rs.getLong(4)).append('\n');
            }
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
        Files.write(file, csv.toString().getBytes("ISO-8859-1"));
        push(file);
    }

    private void push(Path file) throws Exception {
        JSch jsch = new JSch();
        jsch.addIdentity(StartupListener.CONFIG.getProperty("halberd.sftp.key"));
        Session s = jsch.getSession("corvane", StartupListener.CONFIG.getProperty("halberd.sftp.host"), 22);
        s.setConfig("StrictHostKeyChecking", "no");
        s.connect(15000);
        ChannelSftp ch = (ChannelSftp) s.openChannel("sftp");
        ch.connect();
        ch.put(file.toString(), "/inbound/corvane/");
        ch.disconnect();
        s.disconnect();
    }

    private static Properties queries() throws IOException {
        Properties p = new Properties();
        try (InputStream in = NightlyReinsuranceExport.class.getResourceAsStream("/queries.properties")) {
            p.load(in);
        }
        return p;
    }
}
