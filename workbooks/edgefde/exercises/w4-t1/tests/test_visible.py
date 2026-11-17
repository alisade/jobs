"""Visible: FP32 works on the gateway (passes today); INT8 must detect like FP32 (fails today)."""


def test_fp32_detects_faults(built):
    assert built["score"]["fp32"]["recall"] > 0.75


def test_int8_detects_like_fp32(built):
    s = built["score"]
    assert s["fp32"]["recall"] - s["int8"]["recall"] <= 0.02, s
