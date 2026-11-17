package com.corvane.claimdesk.notes;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicLong;

import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/** Propagates X-Request-Id from the portal, or assigns one. */
public class RequestIdFilter implements Filter {

    private final AtomicLong seq = new AtomicLong(1000);

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) throws IOException, ServletException {
        String id = ((HttpServletRequest) request).getHeader("X-Request-Id");
        ((HttpServletResponse) response).setHeader("X-Request-Id", id != null ? id : "cd-" + seq.incrementAndGet());
        chain.doFilter(request, response);
    }
}
