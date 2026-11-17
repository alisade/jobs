#!/usr/bin/env python3
"""Generate the deterministic Salesforce-shaped export used by backend/w1-t1.

Usage: generate.py <out_dir>   writes <out_dir>/export/*.csv, <out_dir>/export/partner_portal/Contact.csv
and <out_dir>/TICKET.md. Same seed, same bytes, every run.
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ALNUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
SUFFIX = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
N_ACCOUNTS = 1200
N_PAIRS = 14
REJECTED_ACCOUNTS = 3


def sf18(id15: str) -> str:
    out = ""
    for chunk in range(3):
        bits = 0
        for i, ch in enumerate(id15[chunk * 5:chunk * 5 + 5]):
            if "A" <= ch <= "Z":
                bits |= 1 << i
        out += SUFFIX[bits]
    return id15 + out


def make_id(rng: random.Random, prefix: str) -> str:
    return prefix + "Hs" + "".join(rng.choice(ALNUM) for _ in range(10))


def sibling(id15: str) -> str:
    # flip the case of the last letter in the random part: same id when compared case-insensitively
    chars = list(id15)
    for i in range(len(chars) - 1, 4, -1):
        if chars[i].isalpha():
            chars[i] = chars[i].swapcase()
            return "".join(chars)
    raise ValueError(id15)


ADJ = ["Brightwater", "Cobalt", "Northgate", "Silverline", "Redwood", "Harbor", "Summit", "Juniper", "Ironbridge",
       "Bluefin", "Granite", "Meridian", "Copperleaf", "Westbrook", "Lakeshore", "Pinecrest", "Starling", "Oakmont"]
NOUN = ["Logistics", "Health", "Analytics", "Foods", "Energy", "Robotics", "Capital", "Media", "Retail", "Labs"]
SUF = ["Inc", "LLC", "Group", "Holdings", "Partners", "Co"]
FIRST = ["Ana", "Ben", "Chen", "Divya", "Eli", "Fatima", "Gus", "Hana", "Ivan", "Jo", "Kofi", "Lena", "Mateo", "Nia"]
LAST = ["Alvarez", "Brooks", "Cho", "Dubois", "Eze", "Fischer", "Garcia", "Haddad", "Ito", "Jensen", "Kumar", "Lopez"]
STAGES = ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]


def write(path: Path, header: list[str], rows: list[list], bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def generate(out: Path) -> dict:
    rng = random.Random(20261103)
    ids15: list[str] = []
    seen = set()
    while len(ids15) < N_ACCOUNTS - N_PAIRS:
        i = make_id(rng, "001")
        if i.lower() not in seen:
            seen.add(i.lower())
            ids15.append(i)
    pair_bases = rng.sample(ids15[: N_ACCOUNTS - N_PAIRS - 10], N_PAIRS)
    for b in pair_bases:
        ids15.append(sibling(b))
    rng.shuffle(ids15)
    accounts = []
    names_used = set()
    id_set = set(ids15)
    rejected = set(rng.sample([i for i in ids15 if i not in pair_bases and sibling(i) not in id_set], REJECTED_ACCOUNTS))
    for i in ids15:
        while True:
            name = f"{rng.choice(ADJ)} {rng.choice(NOUN)} {rng.choice(SUF)}"
            if name in names_used:
                name = f"{rng.choice(ADJ)} {rng.choice(NOUN)} {rng.randrange(2, 99)} {rng.choice(SUF)}"
            if name not in names_used:
                names_used.add(name)
                break
        accounts.append([sf18(i), "" if i in rejected else name, rng.choice(NOUN), rng.choice(["AMER", "EMEA", "APAC"]),
                         rng.choice(["", "Silver", "Gold", "Platinum"])])
    write(out / "export" / "Account.csv", ["Id", "Name", "Industry", "Region__c", "Partner_Tier__c"], accounts)

    pair_ids = set(pair_bases) | {sibling(b) for b in pair_bases}
    contacts, partner = [], []
    contact_ids = []
    def new_contact(acct15: str) -> list:
        cid = sf18(make_id(rng, "003"))
        contact_ids.append(cid)
        f, l = rng.choice(FIRST), rng.choice(LAST)
        return [cid, acct15, f, l, f"{f}.{l}.{len(contact_ids)}@example.com".lower()]
    for _ in range(3000):
        a = rng.choice(ids15)
        row = new_contact(a)
        row[1] = sf18(a)
        contacts.append(row)
    # every collision pair has contacts on both sides, half of them from the 15-char partner extract
    for a in sorted(pair_ids):
        for _ in range(3):
            r = new_contact(a)
            r[1] = sf18(a)
            contacts.append(r)
        partner.append(new_contact(a))
    for _ in range(372):
        partner.append(new_contact(rng.choice(ids15)))
    write(out / "export" / "Contact.csv", ["Id", "AccountId", "FirstName", "LastName", "Email"], contacts, bom=True)
    write(out / "export" / "partner_portal" / "Contact.csv", ["Id", "AccountId", "FirstName", "LastName", "Email"], partner)

    opps = []
    for n in range(900):
        a = rng.choice(ids15)
        opps.append([sf18(make_id(rng, "006")), sf18(a), f"Renewal {n:04d}", rng.choice(STAGES), str(rng.randrange(5, 500) * 1000)])
    write(out / "export" / "Opportunity.csv", ["Id", "AccountId", "Name", "StageName", "Amount"], opps)

    tasks = []
    for n in range(2500):
        who = rng.choice(contact_ids) if rng.random() < 0.8 else ""
        if rng.random() < 0.5:
            what = sf18(rng.choice(ids15))
        else:
            what = rng.choice(opps)[0]
        tasks.append([sf18(make_id(rng, "00T")), who, what, rng.choice(["Call", "Email", "Meeting", "Follow up"]) + f" #{n}"])
    write(out / "export" / "Task.csv", ["Id", "WhoId", "WhatId", "Subject"], tasks)

    a, b = pair_bases[0], sibling(pair_bases[0])
    name_of = {r[0]: r[1] for r in accounts}
    (out / "TICKET.md").write_text(f"""# KEY-4471 Contacts attached to the wrong accounts after the pilot import

Reporter: Dana Whitfield (sales ops)  |  Priority: P2  |  Component: keystone-import

The pilot import into Keystone finished "green" on Monday, but sales ops sees problems in the new UI:

- "{name_of[sf18(b)]}" (legacy id {sf18(b)}) does not exist in Keystone. Its contacts show up under
  "{name_of[sf18(a)]}" (legacy id {sf18(a)}), a different customer in a different region.
- About a dozen accounts are missing in total. The pilot reconciliation report says the Account
  counts differ, and the Account checksum is DIFF, but nobody could explain it from the report.
- A handful of Tasks did not make it across either.
- The import log is full of encoding warnings about a BOM in Contact.csv; one of the team thinks
  that is where the data went wrong.

Tomas Ekberg (migration lead) needs a root cause and a fixed importer before the second pilot wave
(the partner portal app, which still sends 15-character ids) is scheduled.

Attached: the export the pilot used (export/), the pilot import log and reconciliation report (pilot/).
""")
    return {"accounts": len(accounts), "pairs": N_PAIRS, "rejected": REJECTED_ACCOUNTS}


if __name__ == "__main__":
    print(generate(Path(sys.argv[1] if len(sys.argv) > 1 else "incident")))
