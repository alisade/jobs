package com.corvane.claimdesk.web;

import java.io.InputStream;
import java.util.Properties;

import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;

public class StartupListener implements ServletContextListener {

    public static final Properties CONFIG = new Properties();

    @Override
    public void contextInitialized(ServletContextEvent sce) {
        String path = System.getProperty("claimdesk.config", "/etc/claimdesk/claimdesk.properties");
        try (InputStream in = new java.io.FileInputStream(path)) {
            CONFIG.load(in);
        } catch (java.io.IOException e) {
            throw new IllegalStateException("cannot read " + path, e);
        }
    }

    @Override
    public void contextDestroyed(ServletContextEvent sce) {
    }
}
