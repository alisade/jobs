"""Open a DuckDB session over the dataset with the views every query uses.

Views: contact_records (parquet), interval_staffing (csv), change_log (csv). Session TimeZone is UTC,
so local-time work must use timezone('America/New_York', ...) explicitly.
"""

from __future__ import annotations

from pathlib import Path

import duckdb


def connect(data_dir: str | Path = "data") -> duckdb.DuckDBPyConnection:
    d = Path(data_dir)
    if not (d / "contact_records.parquet").exists():
        raise SystemExit(f"no dataset in {d}: run make setup")
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    con.execute(f"CREATE VIEW contact_records AS SELECT * FROM read_parquet('{d / 'contact_records.parquet'}')")
    con.execute(f"CREATE VIEW interval_staffing AS SELECT * FROM read_csv('{d / 'interval_staffing.csv'}', header = true)")
    con.execute(f"CREATE VIEW change_log AS SELECT * FROM read_csv('{d / 'change_log.csv'}', header = true)")
    return con


def run_file(con: duckdb.DuckDBPyConnection, path: str | Path) -> tuple[list[str], list[tuple]]:
    sql = Path(path).read_text()
    rel = con.sql(sql)
    return rel.columns, rel.fetchall()
