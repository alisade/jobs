package com.corvane.claimdesk.notes;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicLong;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

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
