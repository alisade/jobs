import json
import pathlib
import re

import pytest

import kqlcheck as k

EX = pathlib.Path(__file__).resolve().parents[2]
Q = EX / "queries"
SCHEMA = k.parse_table_schema((EX / "schema.kql").read_text())
RAW = json.loads((EX / "data" / "raw_sample.json").read_text())

FORBIDDEN_PROD_OPS = {"take", "limit", "sample"}


def load(name):
    code, strings = k.clean((Q / name).read_text())
    return code, strings


def query(name):
    code, _ = load(name)
    return k.query_body(code)


def summarize_seg(qry):
    segs = k.segments(qry)
    s = [x for x in segs[1:] if k.op_name(x) == "summarize"]
    assert len(s) == 1, f"expected exactly one summarize, found {len(s)}"
    return s[0]


def is_bin(expr, col, seconds):
    m = k.BIN_RE.match(re.sub(r"\s+", " ", expr.strip()))
    if not m:
        return False
    return m.group(1) == col and k.timespan_seconds(m.group(2)) == seconds


# ---------------------------------------------------------------- 01 windows

def test_01_source_and_time_filter_before_summarize():
    qry = query("01_speed_5min.kql")
    segs = k.segments(qry)
    assert segs[0].strip() == "Telemetry"
    names = [k.op_name(s) for s in segs[1:]]
    assert "summarize" in names
    i = names.index("summarize")
    pre = [s for s in segs[1:i + 1] if k.op_name(s) == "where"]
    assert any("Timestamp" in s and "ago(" in s.replace(" ", "") for s in pre), \
        "filter Timestamp > ago(1h) before summarize so the window scan is bounded"


def test_01_group_by_vehicle_and_5m_bin():
    aggs, keys = k.parse_summarize(summarize_seg(query("01_speed_5min.kql")))
    assert len(keys) == 2, f"by-list must have exactly VehicleId and the window, got {keys}"
    exprs = {k.norm(e) for _, e in keys}
    assert "vehicleid" in exprs
    win = [(a, e) for a, e in keys if k.norm(e) != "vehicleid"][0]
    assert is_bin(win[1], "Timestamp", 300), f"window must be bin(Timestamp, 5m), got {win[1]}"
    assert win[0] == "Window", "alias the window column as Window (the tile binds to it)"


def test_01_named_aggregates():
    aggs, _ = k.parse_summarize(summarize_seg(query("01_speed_5min.kql")))
    got = {a: k.norm(e) for a, e in aggs}
    assert got.get("AvgSpeedKph") == "avg(speedkph)"
    assert got.get("MaxEngineTempC") == "max(enginetempc)"
    assert got.get("Readings") == "count()"


def test_01_no_sampling_ops():
    assert not FORBIDDEN_PROD_OPS & set(k.ops(query("01_speed_5min.kql")))


# ---------------------------------------------------------------- 02 latest

def test_02_arg_max_by_vehicle():
    qry = query("02_latest_per_vehicle.kql")
    aggs, keys = k.parse_summarize(summarize_seg(qry))
    assert [k.norm(e) for _, e in keys] == ["vehicleid"]
    assert len(aggs) == 1 and k.norm(aggs[0][1]) == "arg_max(timestamp,*)", \
        f"use arg_max(Timestamp, *) to keep the whole latest row, got {aggs}"


def test_02_no_top_take_sort_shortcuts():
    names = k.ops(query("02_latest_per_vehicle.kql"))
    assert not ({"take", "limit", "top", "distinct"} & set(names))
    i = names.index("summarize")
    assert "sort" not in names[:i], "sorting before summarize is wasted work"


def test_02_bounded_scan_and_output_columns():
    qry = query("02_latest_per_vehicle.kql")
    segs = k.segments(qry)
    names = [k.op_name(s) for s in segs[1:]]
    i = names.index("summarize")
    assert any(k.op_name(s) == "where" and "ago(" in s.replace(" ", "") for s in segs[1:i + 1])
    proj = [s for s in segs[i + 2:] if k.op_name(s) in ("project", "project-rename", "project-reorder")]
    assert proj, "project the documented output columns after summarize"
    cols = [a or e.strip() for a, e in k.parse_list(proj[-1], k.op_name(proj[-1]))]
    assert cols[:6] == ["VehicleId", "LastSeen", "SpeedKph", "FuelPct", "Lat", "Lon"], cols


# ---------------------------------------------------------------- 03 update policy

def _func_and_policy():
    code, strings = load("03_update_policy.kql")
    cmds = k.mgmt_commands(code)
    func = [c for c in cmds if re.match(r"\.create(-or-alter)?\s+function", c, re.I)]
    pol = [c for c in cmds if re.match(r"\.alter\s+table\s+Telemetry\s+policy\s+update", c, re.I)]
    return func, pol, strings


def _func_body():
    func, _, _ = _func_and_policy()
    assert len(func) == 1, "one .create-or-alter function command"
    m = re.search(r"\)\s*\{(.*)\}\s*$", func[0], re.S)
    assert m, "function body in { }"
    assert re.search(r"\bParseRawTelemetry\s*\(\s*\)", func[0])
    return m.group(1)


CAST = {"datetime": {"todatetime"}, "string": {"tostring"}, "real": {"toreal", "todouble"},
        "long": {"tolong"}, "int": {"toint"}, "bool": {"tobool"}, "dynamic": {"todynamic"}}


def _final_projection(body):
    segs = k.segments(k.query_body(body))
    assert segs[0].strip() == "RawTelemetry", "the function must read RawTelemetry by its plain name"
    names = [k.op_name(s) for s in segs[1:]]
    idx = max(i for i, n in enumerate(names) if n == "project")
    after = names[idx + 1:]
    assert all(n == "where" for n in after), "only filters may follow the final project"
    return k.parse_list(segs[1 + idx], "project")


def test_03_function_projects_target_schema_in_order():
    items = _final_projection(_func_body())
    target = SCHEMA["Telemetry"]
    assert [a for a, _ in items] == [c for c, _ in target], \
        "update policy output must match the target table column names and order"


def test_03_function_casts_match_types():
    items = _final_projection(_func_body())
    for (name, expr), (_, typ) in zip(items, SCHEMA["Telemetry"]):
        fn = re.match(r"^(\w+)\(", expr.strip())
        assert fn and fn.group(1).lower() in CAST[typ], f"{name}: {typ} needs one of {CAST[typ]}, got {expr}"


def _has_path(obj, path):
    cur = obj
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return False
        cur = cur[p]
    return True


def test_03_function_paths_exist_in_payload():
    items = _final_projection(_func_body())
    for name, expr in items:
        m = re.search(r"Payload((?:\.\w+|\[\"__S\d+__\"\])+)", expr)
        assert m, f"{name} must be extracted from Payload"
        path = re.findall(r"\.(\w+)", m.group(1))
        assert all(_has_path(ev, path) for ev in RAW), f"{name}: Payload.{'.'.join(path)} not in raw_sample.json"


def test_03_function_drops_bad_rows():
    body = k.query_body(_func_body())
    segs = k.segments(body)
    wheres = " ".join(s for s in segs[1:] if k.op_name(s) == "where")
    w = k.norm(wheres)
    assert "timestamp" in w and ("isnotnull(timestamp)" in w or "isnull(timestamp)" in w)
    assert "isnotempty(vehicleid)" in w or "isempty(vehicleid)" in w


def test_03_policy_object():
    _, pol, strings = _func_and_policy()
    assert len(pol) == 1, "one .alter table Telemetry policy update command"
    lits = re.findall(r'"__S(\d+)__"', pol[0])
    assert lits, "policy JSON must be a string literal"
    obj = k.json_from_literal(strings[int(lits[0])])
    assert isinstance(obj, list) and len(obj) == 1
    p = obj[0]
    allowed = {"IsEnabled", "Source", "Query", "IsTransactional", "PropagateIngestionProperties",
               "SourceIsWildCard", "ManagedIdentity"}
    assert set(p) <= allowed, f"unknown keys {set(p) - allowed}"
    assert p.get("IsEnabled") is True
    assert p.get("Source") == "RawTelemetry"
    assert re.fullmatch(r"\s*ParseRawTelemetry\(\s*\)\s*", p.get("Query", ""))
    assert p.get("IsTransactional") is True, "production policy must be transactional"
    assert isinstance(p.get("PropagateIngestionProperties"), bool)


# ---------------------------------------------------------------- 04 materialized view

MV_RE = re.compile(
    r"^\.create\s+(?P<async>async\s+)?(?:ifnotexists\s+)?materialized-view\s+"
    r"(?:with\s*\((?P<props>[^)]*)\)\s*)?(?P<name>\w+)\s+on\s+table\s+(?P<src>\w+)\s*\{(?P<q>.*)\}\s*$",
    re.S | re.I,
)


def _mv():
    code, _ = load("04_materialized_view.kql")
    cmds = [c for c in k.mgmt_commands(code) if c.startswith(".")]
    assert len(cmds) == 1, "exactly one .create materialized-view command"
    m = MV_RE.match(cmds[0])
    assert m, "command does not match .create [async] [ifnotexists] materialized-view [with(...)] Name on table T { Q }"
    props = {}
    for part in k.split_top(m.group("props") or "", ","):
        if "=" in part:
            a, b = part.split("=", 1)
            props[a.strip().lower()] = b.strip()
    return m, props


def test_04_command_shape():
    m, props = _mv()
    assert m.group("name") == "TelemetryDedup" and m.group("src") == "Telemetry"


def test_04_backfill_requires_async():
    m, props = _mv()
    assert props.get("backfill", "false").lower() == "true", "backfill existing rows"
    assert m.group("async"), "backfill=true requires .create async"


def test_04_lookback_bounded():
    _, props = _mv()
    assert "lookback" in props, "set lookback so materialization does not rescan the whole view"
    secs = k.timespan_seconds(props["lookback"])
    assert secs is not None and 0 < secs <= 86400, "lookback should be hours, not days or weeks"


def test_04_query_rules():
    m, _ = _mv()
    q = k.query_body(m.group("q"))
    names = k.ops(q)
    assert names and names[-1] == "summarize", "summarize must be the last operator"
    assert names.count("summarize") == 1
    assert not {"sort", "top", "take", "limit", "partition", "serialize"} & set(names)
    assert "ago(" not in q.replace(" ", "") and "now(" not in q.replace(" ", ""), \
        "no now()-dependent filters in a materialized view; use retention instead"
    aggs, keys = k.parse_summarize(k.segments(q)[-1])
    assert [k.norm(e) for _, e in keys] == ["eventid"]
    assert len(aggs) == 1 and k.norm(aggs[0][1]) in ("take_any(*)", "arg_max(timestamp,*)")


# ---------------------------------------------------------------- 05 trips

def test_05_dedup_source():
    qry = query("05_trips.kql")
    segs = k.segments(qry)
    src = segs[0].strip()
    dedup_inline = any(
        k.op_name(s) == "summarize" and "byeventid" in k.norm(s) for s in segs[1:]
    ) or any(k.op_name(s) == "distinct" for s in segs[1:])
    assert src == "TelemetryDedup" or dedup_inline, "trips must not double count retried events"


def test_05_session_logic():
    qry = query("05_trips.kql")
    flat = k.norm(qry)
    uses_rws = "row_window_session(" in flat
    uses_prev = "prev(" in flat and "row_cumsum(" in flat
    uses_scan = "|scan" in flat and "step" in flat
    assert uses_rws or uses_prev or uses_scan, "use row_window_session, prev()+row_cumsum, or scan"
    if uses_rws:
        call = qry[qry.find("row_window_session("):]
        depth, end = 0, 0
        for i, ch in enumerate(call):
            depth += ch == "("
            depth -= ch == ")"
            if depth == 0 and ch == ")":
                end = i
                break
        args = k.split_top(call[len("row_window_session("):end], ",")
        assert len(args) == 4, "pass the restart condition so trips do not span vehicles"
        assert k.timespan_seconds(args[1]) == 12 * 3600, "max trip length 12h"
        assert k.timespan_seconds(args[2]) == 600, "gap between neighbors 10m"
        assert "vehicleid" in k.norm(args[3]) and "prev(" in k.norm(args[3])
    else:
        assert "10m" in flat or "600s" in flat or "10min" in flat, "10 minute gap threshold"


def test_05_ascending_order_per_vehicle():
    qry = query("05_trips.kql")
    flat = k.norm(qry)
    if "|scan" in flat and "partitionhint" in flat:
        return
    segs = k.segments(qry)
    sorts = [s for s in segs[1:] if k.op_name(s) == "sort"]
    assert sorts, "session functions need serialized, ordered input"
    s = k.norm(sorts[0])
    assert "vehicleid" in s, "order by VehicleId first so each vehicle is contiguous"
    assert "timestampasc" in s, "Timestamp must be explicitly asc (sort defaults to desc)"


def test_05_output_columns():
    qry = query("05_trips.kql")
    segs = k.segments(qry)
    summ = [s for s in segs[1:] if k.op_name(s) == "summarize"]
    assert summ
    aggs, keys = k.parse_summarize(summ[-1])
    names = {a or e for a, e in aggs} | {a or e.strip() for a, e in keys}
    for col in ("VehicleId", "TripStart", "TripEnd", "Readings", "MaxSpeedKph"):
        assert col in names, f"missing output column {col}"
    assert "VehicleId" in {a or e.strip() for a, e in keys}


# ---------------------------------------------------------------- hygiene

@pytest.mark.parametrize("name", sorted(p.name for p in Q.glob("*.kql")))
def test_no_todo_left(name):
    assert "TODO" not in (Q / name).read_text()
