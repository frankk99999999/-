"""Generate a realistic ad-event stream and bulk-load it into ClickHouse.

This is the *high-volume* path. We simulate the funnel:
    impression  (we pay `cost`)
      -> click  (some probability, conditional on impression)
        -> conversion  (some probability, conditional on click; carries `revenue`)

We insert in batches so we never hold the whole dataset in memory --
the same discipline a real ingestion service needs at 10k events/s.
"""

from __future__ import annotations

import random
import time
from datetime import datetime, timedelta

import clickhouse_connect

from .config import SIM
from .db import ch_client, pg_conn

CHANNEL_CTR = {"meta": 0.012, "google": 0.018, "tiktok": 0.009}
CHANNEL_CVR = {"meta": 0.03, "google": 0.045, "tiktok": 0.02}
# Cost is billed per *thousand impressions* (CPM), like real ad platforms.
CHANNEL_CPM = {"meta": 14.0, "google": 22.0, "tiktok": 9.0}
AVG_ORDER_VALUE = 65.0  # revenue per conversion

BATCH_SIZE = 20_000


def _campaigns() -> list[dict]:
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, account_id, channel, daily_budget FROM campaigns")
        # psycopg returns NUMERIC as Decimal and BIGINT as int; normalise to
        # plain Python numerics so arithmetic and ClickHouse inserts are happy.
        return [
            {
                "id": int(r["id"]),
                "account_id": int(r["account_id"]),
                "channel": r["channel"],
                "daily_budget": float(r["daily_budget"]),
            }
            for r in cur.fetchall()
        ]


def _quality_factor(campaign_id: int) -> float:
    """A stable per-campaign 'how well does this ad work' multiplier.

    Seeded by campaign_id so the same campaign always has the same
    quality across runs. It scales CTR and CVR together, so its effect
    on ROAS is roughly squared -- hence the narrow range. The point is
    to give the agent a *spread* of ROAS (some campaigns well below the
    target, some well above) so its decisions are interesting.
    """
    return random.Random(campaign_id).uniform(0.5, 2.0)


def generate_rows(campaigns: list[dict], rng: random.Random):
    """Yield event rows across the simulated window, one impression at a time."""
    now = datetime.utcnow().replace(microsecond=0)
    start = now - timedelta(days=SIM.days)

    for day in range(SIM.days):
        day_start = start + timedelta(days=day)
        for camp in campaigns:
            cpm = CHANNEL_CPM[camp["channel"]]
            cost_per_impression = cpm / 1000.0
            quality = _quality_factor(camp["id"])
            ctr = CHANNEL_CTR[camp["channel"]] * quality
            cvr = CHANNEL_CVR[camp["channel"]] * quality

            # Budget caps how many impressions we can afford in a day.
            max_affordable = int(camp["daily_budget"] / cost_per_impression)
            n = min(SIM.impressions_per_day, max(0, max_affordable))

            for _ in range(n):
                ts = day_start + timedelta(seconds=rng.randint(0, 86_399))
                user_id = rng.randint(1, 5_000_000)

                impression_id = f"imp_{user_id}_{int(ts.timestamp())}_{rng.randint(0,9999)}"
                yield (
                    ts, camp["account_id"], camp["id"], user_id,
                    "impression", cost_per_impression, 0.0, impression_id, "", "",
                )

                if rng.random() < ctr:
                    click_id = f"clk_{user_id}_{int(ts.timestamp())}_{rng.randint(0,9999)}"
                    yield (
                        ts, camp["account_id"], camp["id"], user_id,
                        "click", 0.0, 0.0, impression_id, click_id, "",
                    )
                    if rng.random() < cvr:
                        conversion_id = f"cnv_{user_id}_{int(ts.timestamp())}_{rng.randint(0,9999)}"
                        revenue = round(rng.gauss(AVG_ORDER_VALUE, 20), 2)
                        yield (
                            ts, camp["account_id"], camp["id"], user_id,
                            "conversion", 0.0, max(revenue, 5.0),
                            impression_id, click_id, conversion_id,
                        )


def load_clickhouse() -> None:
    rng = random.Random(SIM.seed)
    campaigns = _campaigns()
    if not campaigns:
        raise SystemExit("No campaigns found. Run seed_oltp first.")

    client = ch_client()
    client.command("TRUNCATE TABLE converge.events")
    # The rollup is fed by a materialized view, so truncating the source
    # does NOT clear it. Clear it explicitly to keep re-runs idempotent.
    client.command("TRUNCATE TABLE converge.campaign_daily_stats")

    columns = [
        "event_time", "account_id", "campaign_id", "user_id",
        "event_type", "cost", "revenue",
        "impression_id", "click_id", "conversion_id",
    ]

    batch: list[tuple] = []
    total = 0
    t0 = time.time()
    for row in generate_rows(campaigns, rng):
        batch.append(row)
        if len(batch) >= BATCH_SIZE:
            client.insert("converge.events", batch, column_names=columns)
            total += len(batch)
            batch.clear()

    if batch:
        client.insert("converge.events", batch, column_names=columns)
        total += len(batch)

    elapsed = time.time() - t0
    print(f"ClickHouse loaded: {total:,} events in {elapsed:.1f}s "
          f"({total / max(elapsed, 1e-9):,.0f} events/s)")


if __name__ == "__main__":
    load_clickhouse()
