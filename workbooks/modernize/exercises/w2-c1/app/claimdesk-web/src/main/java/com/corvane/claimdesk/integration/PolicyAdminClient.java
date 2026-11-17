package com.corvane.claimdesk.integration;

import java.net.URL;

import javax.enterprise.context.ApplicationScoped;
import javax.xml.namespace.QName;
import javax.xml.ws.Service;

import com.corvane.claimdesk.web.StartupListener;

/** SOAP client for the policy administration system (PAS 6, mainframe-fronted). */
@ApplicationScoped
public class PolicyAdminClient {

    private static final QName SERVICE = new QName("urn:corvane:pas:policy:2", "PolicyInquiryService");

    public PolicyInquiry port() throws java.net.MalformedURLException {
        URL wsdl = new URL(StartupListener.CONFIG.getProperty("policyadmin.wsdl"));
        return Service.create(wsdl, SERVICE).getPort(PolicyInquiry.class);
    }

    public interface PolicyInquiry {
        String coverageStatus(String policyNumber, String lossDate);
    }
}
