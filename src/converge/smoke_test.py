"""End-to-end smoke test: the whole loop in one command.

    seed OLTP -> generate events into OLAP -> query metrics -> agent decides -> write back

If this runs clean, the platform skeleton is alive:
data flows in, gets aggregated at speed, drives a decision, and the
decision is durably recorded.
"""

from __future__ import annotations

import time

from .agent import run_once
from .attribution import campaign_roas, time_both
from .generate_events import load_clickhouse
from .seed_oltp import seed_postgres


def main() -> None:
    print("=" * 60)
    print("MINI CONVERGE -- end-to-end smoke test")
    print("=" * 60)

    print("\n[1/5] Seeding Postgres (OLTP)...")
    seed_postgres()

    print("\n[2/5] Generating + loading ClickHouse (OLAP)...")
    load_clickhouse()

    print("\n[3/5] Querying metrics...")
    rows = campaign_roas()
    print(f"  {len(rows)} campaigns with metrics")
    for r in rows[:5]:
        print(f"    campaign {r['campaign_id']}: "
              f"cost=${r['total_cost']:.0f} revenue=${r['total_revenue']:.0f} roas={r['roas']:.2f}")

    print("\n[4/5] Raw scan vs. materialized rollup:")
    time_both()

    print("\n[5/5] Running the budget agent...")
    decisions = run_once()
    changes = [d for d in decisions if d["action"] != "hold"]
    print(f"  evaluated {len(decisions)} campaigns, {len(changes)} changes")
    for d in changes[:10]:
        print(f"    camp {d['campaign_id']}: {d['action']:>8} "
              f"{d['old_budget']:.0f} -> {d['new_budget']:.0f}")

    print("\nDone. The loop works end-to-end.")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\nTotal: {time.time() - t0:.1f}s")
