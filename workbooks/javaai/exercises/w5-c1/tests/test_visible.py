from rag.chunking import heading_chunks
from rag.corpus import load_lessons
from rag.metrics import recall_at_k


def test_heading_chunks_cite_sections():
    lesson = load_lessons()[0]
    chunks = heading_chunks(lesson)
    assert [c.section_id for c in chunks] == [s.id for s in lesson.sections]


def test_recall_simple_case():
    assert recall_at_k(["l4-s2", "l4-s1"], {"l4-s1"}, 5) == 1.0
