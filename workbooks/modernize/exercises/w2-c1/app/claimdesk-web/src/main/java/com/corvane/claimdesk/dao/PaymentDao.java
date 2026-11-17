package com.corvane.claimdesk.dao;

import java.math.BigDecimal;

import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

import com.corvane.claimdesk.model.Payment;

@Stateless
public class PaymentDao {

    @PersistenceContext(unitName = "claimdesk")
    private EntityManager em;

    public long record(String claimNumber, BigDecimal amount, String approvedBy) {
        Payment p = new Payment(claimNumber, amount, approvedBy);
        em.persist(p);
        em.flush();
        return p.getId();
    }
}
