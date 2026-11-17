"""Visible tests. make test"""

from conftest import END, START

from sampling.population import build_population, completeness, sample_size


def test_population_reconciles_to_the_control_total(ex):
    pop = build_population(ex["prs"], ex["deploys"], START, END)
    rec = completeness(pop, ex["total"])
    assert rec.reconciled, rec.differences
    assert rec.population_count == 220


def test_sample_size_for_a_recurring_control(ex):
    assert sample_size(ex["table"], "recurring") == 25
