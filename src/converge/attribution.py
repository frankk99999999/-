"""Attribution & metrics: the analytical queries the agent reads.

Two ways to compute per-campaign ROAS:

  1. RAW: scan the `events` table and aggregate on the fly. Correct,
     but cost scales with the number of raw rows.
  2. ROLLUP: read the pre-aggregated `campaign_daily_stats` table that
     ClickHouse keeps up to date via the materialized view. Tiny, fast.

We expose both so you can literally time the difference -- that is the
core lesson of the "materialize the attribution dataset" problem.
"""

from __future__ import annotations

import time

from .config import AGENT
from .db import ch_client

# ---- ROAS over a rolling window, straight off the raw event stream ----
RAW_ROAS_SQL = """
SELECT
    campaign_id,
    sum(cost)                                          AS total_cost,
    sum(revenue)                                       AS total_revenue,
    if(sum(cost) = 0, 0, sum(revenue) / sum(cost))     AS roas,
    countIf(event_type = 'conversion')                 AS conversions
FROM converge.events
WHERE event_time >= now() - INTERVAL {days} DAY
GROUP BY campaign_id
ORDER BY roas DESC
"""

# ---- Same numbers, but read the pre-aggregated rollup instead ----
ROLLUP_ROAS_SQL = """
SELECT
    campaign_id,
    sum(cost)                                          AS total_cost,
    sum(revenue)                                       AS total_revenue,
    if(sum(cost) = 0, 0, sum(revenue) / sum(cost))     AS roas,
    sum(conversions)                                   AS conversions
FROM converge.campaign_daily_stats
WHERE event_date >= today() - {days}
GROUP BY campaign_id
ORDER BY roas DESC
"""


def campaign_roas(days: int | None = None, *, use_rollup: bool = True) -> list[dict]:
    days = days or AGENT.lookback_days
    sql = (ROLLUP_ROAS_SQL if use_rollup else RAW_ROAS_SQL).format(days=days)
    client = ch_client()
    result = client.query(sql)
    cols = result.column_names
    return [dict(zip(cols, row)) for row in result.result_rows]


def time_both(days: int | None = None) -> None:
    """Time the raw scan vs. the materialized rollup. Run after loading data."""
    days = days or AGENT.lookback_days
    client = ch_client()
    for label, sql in (("raw scan", RAW_ROAS_SQL), ("rollup", ROLLUP_ROAS_SQL)):
        t0 = time.perf_counter()
        rows = client.query(sql.format(days=days)).result_rows
        dt = (time.perf_counter() - t0) * 1000
        print(f"{label:>10}: {dt:8.1f} ms  ({len(rows)} campaigns)")


if __name__ == "__main__":
    time_both()
