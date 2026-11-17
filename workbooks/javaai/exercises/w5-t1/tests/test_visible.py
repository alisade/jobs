from pathlib import Path

from ingest.build_index import ingest

CORPUS = Path(__file__).resolve().parent.parent / "corpus"


def test_every_section_is_indexed():
    rows = ingest(CORPUS)
    assert len(rows) == 2 + 4 + 4 + 3


def test_rows_carry_the_course():
    assert {r.course for r in ingest(CORPUS)} == {"bio-210"}
