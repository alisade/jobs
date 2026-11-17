"""Visible test: the exported population reconciles to the deploy log. make test"""

from popexport import client, population
from popexport.fakeapi import FakeGitHub


def test_population_reconciles():
    res = population.build(client.fetch_closed_pulls(FakeGitHub(), "mfh/tms-core"))
    assert res["reconciled"], res
