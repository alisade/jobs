package com.corvane.claimdesk.rating;

import java.math.BigDecimal;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlType;

/** One rated claim, as sent to the reinsurer (Halberd Re) in the nightly rating feed. */
@XmlRootElement(name = "ratingResult", namespace = "urn:corvane:claims:rating:1")
@XmlAccessorType(XmlAccessType.FIELD)
@XmlType(propOrder = {"policyNumber", "insuredName", "lossCause", "grossLoss", "retention", "cededLoss"})
public class RatingResult {

    @XmlAttribute(name = "id", required = true)
    private String id;

    @XmlElement(namespace = "urn:corvane:claims:rating:1", required = true)
    private String policyNumber;

    @XmlElement(namespace = "urn:corvane:claims:rating:1", required = true)
    private String insuredName;

    @XmlElement(namespace = "urn:corvane:claims:rating:1", required = true)
    private String lossCause;

    @XmlElement(namespace = "urn:corvane:claims:rating:1", required = true)
    private BigDecimal grossLoss;

    @XmlElement(namespace = "urn:corvane:claims:rating:1", required = true)
    private BigDecimal retention;

    @XmlElement(namespace = "urn:corvane:claims:rating:1", required = true)
    private BigDecimal cededLoss;

    public RatingResult() {
        // JAXB
    }

    public RatingResult(String id, String policyNumber, String insuredName, String lossCause,
                        BigDecimal grossLoss, BigDecimal retention, BigDecimal cededLoss) {
        this.id = id;
        this.policyNumber = policyNumber;
        this.insuredName = insuredName;
        this.lossCause = lossCause;
        this.grossLoss = grossLoss;
        this.retention = retention;
        this.cededLoss = cededLoss;
    }

    public String getId() { return id; }
    public String getPolicyNumber() { return policyNumber; }
    public String getInsuredName() { return insuredName; }
    public String getLossCause() { return lossCause; }
    public BigDecimal getGrossLoss() { return grossLoss; }
    public BigDecimal getRetention() { return retention; }
    public BigDecimal getCededLoss() { return cededLoss; }
}
