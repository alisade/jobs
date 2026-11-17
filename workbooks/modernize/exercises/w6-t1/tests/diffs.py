"""Small unified diffs used by the tests."""


def mk(path, removed=(), added=(), header_extra="", old=None):
    old = old or path
    body = "".join(f"-{l}\n" for l in removed) + "".join(f"+{l}\n" for l in added)
    return (f"diff --git a/{old} b/{path}\n{header_extra}index 1111111..2222222 100644\n"
            f"--- a/{old}\n+++ b/{path}\n@@ -1,{len(removed)} +1,{len(added)} @@\n{body}")


MAIN = "claimdesk-rating/src/main/java/com/corvane/claimdesk/rating/PremiumCalculator.java"
TEST = "claimdesk-rating/src/test/java/com/corvane/claimdesk/rating/PremiumCalculatorTest.java"
GOLDEN = "claimdesk-rating/src/test/resources/golden/bordereau-2026-10.json"

PRODUCTION_ONLY = mk(MAIN, ["        return raw.setScale(2, BigDecimal.ROUND_HALF_UP);"],
                     ["        return raw.setScale(2, RoundingMode.HALF_UP);"])
