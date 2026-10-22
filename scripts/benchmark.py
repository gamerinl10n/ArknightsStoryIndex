"""Read-only local benchmark; reports timings/counts, never dialogue text."""

import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import statistics
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from core import search
from runtime_snapshot import materialize


def benchmark(database, rounds=15):
    path = materialize(database)
    report = {}
    with closing(
        sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
    ) as db:
        db.row_factory = sqlite3.Row
        for label, args in [("pair_ko", ("M3", "켈시")), ("solo_ko", ("아미야",))]:
            for detailed in (True, False):
                times = []
                statements = []
                for _ in range(rounds):
                    seen = []
                    db.set_trace_callback(seen.append)
                    start = perf_counter()
                    data = search(db, *args, include_details=detailed)
                    times.append((perf_counter() - start) * 1000)
                    statements.append(len(seen))
                report[label + ("_detailed" if detailed else "_light")] = {
                    "total": data["total"],
                    "page_items": len(data["items"]),
                    "sql_statements": max(statements),
                    "response_bytes": len(
                        json.dumps(data, ensure_ascii=False).encode()
                    ),
                    "median_ms": round(statistics.median(times), 2),
                    "p95_ms": round(
                        sorted(times)[min(len(times) - 1, int(len(times) * 0.95))], 2
                    ),
                }
    client = create_app(str(path), readonly=True).test_client()
    times = []
    for _ in range(rounds):
        start = perf_counter()
        response = client.get("/api/suggestions?lang=ko_KR")
        if response.status_code != 200:
            raise RuntimeError("Suggestions unavailable")
        times.append((perf_counter() - start) * 1000)
    report["suggestions_ko"] = {
        "items": len(response.json),
        "first_ms": round(times[0], 2),
        "warm_median_ms": round(statistics.median(times[1:]), 2),
    }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("database")
    parser.add_argument("--rounds", type=int, default=15)
    args = parser.parse_args()
    if args.rounds < 2:
        parser.error("At least two rounds are required")
    print(
        json.dumps(benchmark(args.database, args.rounds), ensure_ascii=False, indent=2)
    )
