package com.corvane.claimdesk.notes;

import java.io.File;
import java.nio.file.Files;

import org.apache.catalina.Context;
import org.apache.catalina.LifecycleException;
import org.apache.catalina.startup.Tomcat;
import org.apache.tomcat.util.descriptor.web.ErrorPage;
import org.apache.tomcat.util.descriptor.web.FilterDef;
import org.apache.tomcat.util.descriptor.web.FilterMap;

/** Embedded container for the notes service. start(0) picks a free port (tests). */
public final class NotesServer {

    private final Tomcat tomcat = new Tomcat();

    public int start(int port, ClaimRepository repo) throws Exception {
        File base = Files.createTempDirectory("claimdesk-notes").toFile();
        tomcat.setBaseDir(base.getAbsolutePath());
        tomcat.setPort(port);
        tomcat.getConnector();
        Context ctx = tomcat.addContext("/claimdesk", base.getAbsolutePath());

        Tomcat.addServlet(ctx, "claims", new ClaimServlet(repo));
        ctx.addServletMappingDecoded("/claims", "claims");
        ctx.addServletMappingDecoded("/claims/*", "claims");
        Tomcat.addServlet(ctx, "error", new ErrorServlet());
        ctx.addServletMappingDecoded("/error", "error");

        ErrorPage any = new ErrorPage();
        any.setLocation("/error");
        ctx.addErrorPage(any);

        FilterDef fd = new FilterDef();
        fd.setFilterName("requestId");
        fd.setFilter(new RequestIdFilter());
        ctx.addFilterDef(fd);
        FilterMap fm = new FilterMap();
        fm.setFilterName("requestId");
        fm.addURLPattern("/*");
        ctx.addFilterMap(fm);

        tomcat.start();
        return tomcat.getConnector().getLocalPort();
    }

    public void stop() throws LifecycleException {
        tomcat.stop();
        tomcat.destroy();
    }

    public static void main(String[] args) throws Exception {
        NotesServer s = new NotesServer();
        int port = s.start(args.length > 0 ? Integer.parseInt(args[0]) : 8080, ClaimRepository.seeded());
        System.out.println("claimdesk-notes on http://localhost:" + port + "/claimdesk/claims?status=OPEN");
        s.tomcat.getServer().await();
    }
}
