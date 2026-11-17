"""python -m oidccheck <trust-policy.json> <claims.json> [account]"""
import json
import sys

from .engine import check

pol = json.load(open(sys.argv[1]))
claims = json.load(open(sys.argv[2]))
acct = sys.argv[3] if len(sys.argv) > 3 else "111100000004"
ok, why = check(pol, claims, acct)
print(("ALLOW " if ok else "DENY  ") + why)
