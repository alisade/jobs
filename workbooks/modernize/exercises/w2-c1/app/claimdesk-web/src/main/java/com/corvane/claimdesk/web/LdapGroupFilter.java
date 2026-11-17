package com.corvane.claimdesk.web;

import java.io.IOException;
import java.util.Hashtable;

import javax.naming.Context;
import javax.naming.NamingEnumeration;
import javax.naming.directory.DirContext;
import javax.naming.directory.InitialDirContext;
import javax.naming.directory.SearchControls;
import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/** Second check on payments: the user must be a direct member of the payments group in LDAP. */
public class LdapGroupFilter implements Filter {

    private String requiredGroup;

    @Override
    public void init(FilterConfig cfg) {
        requiredGroup = cfg.getInitParameter("requiredGroup");
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) throws IOException, ServletException {
        HttpServletRequest req = (HttpServletRequest) request;
        if (!isMember(req.getRemoteUser())) {
            ((HttpServletResponse) response).sendError(HttpServletResponse.SC_FORBIDDEN);
            return;
        }
        chain.doFilter(request, response);
    }

    private boolean isMember(String uid) {
        Hashtable<String, String> env = new Hashtable<>();
        env.put(Context.INITIAL_CONTEXT_FACTORY, "com.sun.jndi.ldap.LdapCtxFactory");
        env.put(Context.PROVIDER_URL, StartupListener.CONFIG.getProperty("ldap.url"));
        env.put(Context.SECURITY_PRINCIPAL, StartupListener.CONFIG.getProperty("ldap.bindDn"));
        env.put(Context.SECURITY_CREDENTIALS, StartupListener.CONFIG.getProperty("ldap.bindPassword"));
        try {
            DirContext ctx = new InitialDirContext(env);
            SearchControls sc = new SearchControls();
            sc.setSearchScope(SearchControls.OBJECT_SCOPE);
            NamingEnumeration<?> hits = ctx.search(requiredGroup, "(member=uid=" + uid + ",ou=people,dc=corvane,dc=local)", sc);
            boolean member = hits.hasMore();
            ctx.close();
            return member;
        } catch (javax.naming.NamingException e) {
            return false;
        }
    }

    @Override
    public void destroy() {
    }
}
