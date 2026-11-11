# Mini Converge

A single-person, local reproduction of the *shape* of
[Converge](https://www.ycombinator.com/companies) — the NYC company building
**agents that buy and scale ads** for consumer brands (Hims & Hers, etc.).

Real Converge runs an agent that makes >90% of all budget changes in an ad
account, across $1M+ of daily budget, on infrastructure ingesting 20 TB/month
and handling 10k jobs/s. This repo reproduces the **architecture and the hard
parts** of that platform at laptop scale, so you can learn (and talk about) the
real system by building a small one.

It is a *learning reproduction*, not a clone. See
[docs/vs-converge.md](docs/vs-converge.md) for exactly what's faithful and
what's simplified.

---

## What this actually is

One closed loop, end to end:

```
   Postgres (OLTP)                 ClickHouse (OLAP)                 Agent
  ┌───────────────┐   campaigns   ┌──────────────────────┐   metrics  ┌────────┐
  │ ad_accounts   │──────────────▶│ events (raw firehose)│───────────▶│ decide │
  │ campaigns     │               │   │ materialized view│            │ + audit│
  │ agent_actions │◀──────────────│   ▼                  │◀───────────│ write  │
  └───────────────┘   writeback   │ campaign_daily_stats │  decisions └────────┘
        ▲                          └──────────────────────┘
        └──────────────── budget changes ────────────────────────────────┘
```

1. **OLTP (Postgres):** the small, mutable, strongly-consistent state — accounts,
   campaigns, and every decision the agent makes (audit trail).
2. **OLAP (ClickHouse):** the high-volume, append-only event firehose
   (impressions / clicks / conversions), plus a `SummingMergeTree` rollup kept
   current by a materialized view.
3. **The agent:** reads aggregated metrics, decides to increase / decrease / hold
   a campaign's budget, and writes the change + reason back to Postgres.

The interesting engineering is all in *how data flows between those three*.

---

## Quickstart

Requirements: Docker, Docker Compose, Python 3.11+.

```bash
# 1. Python deps
pip install -r requirements.txt

# 2. Config
cp .env.example .env

# 3. Start the databases
make up

# 4. Run the whole loop (seed -> load -> query -> decide -> write back)
make smoke
```

Expected output ends with something like:

```
ClickHouse loaded: 5,691,838 events in 26.2s (216,917 events/s)
...
raw scan:     79.6 ms  (40 campaigns)
  rollup:      4.9 ms  (40 campaigns)
...
evaluated 40 campaigns, 27 changes
Done. The loop works end-to-end.
```

### Individual steps

```bash
make seed        # Postgres: accounts + campaigns
make events      # ClickHouse: generate + load the event firehose
make metrics     # time the raw scan vs. the materialized rollup
make agent-dry   # run the agent WITHOUT writing changes
make agent       # run the agent for real (writes to Postgres)
make down        # stop the databases (keeps data)
make clean       # stop AND delete all data
```

---

## Layout

```
docker-compose.yml            Postgres + ClickHouse, one command
sql/postgres_init.sql         OLTP schema (accounts, campaigns, agent_actions)
sql/clickhouse_init.sql       OLAP schema (events + rollup + materialized view)
src/converge/
  config.py                   env-driven config
  db.py                       connection helpers for both databases
  seed_oltp.py                seed Postgres (the small, mutable state)
  generate_events.py          simulate the ad funnel -> bulk-load ClickHouse
  attribution.py              the ROAS queries: raw scan vs. materialized rollup
  agent.py                    read metrics -> decide -> write back (audited)
  smoke_test.py               the whole loop in one command
docs/
  schema.md                   the data model, and *why* each table lives where
  vs-converge.md              what's faithful to real Converge, what's not
```

---

## The three lessons this repo is built to teach

1. **Right database for the right job.** Accounts and decisions go in Postgres;
   billions of events go in ClickHouse. Mixing them is how systems fall over.
2. **Materialize the expensive join.** Recomputing ROAS from raw events on every
   query is correct but slow; a `SummingMergeTree` fed by a materialized view is
   ~10-20x faster at this scale and gets *more* valuable as data grows. This is
   the "materialize the attribution dataset" problem from the job description.
3. **An agent that moves money needs an audit trail.** Every budget change is
   clamped, reasoned, and recorded, so it is inspectable and reversible.

---

## Next steps (the roadmap)

This MVP deliberately stops short of the hard parts. Good next moves:

- **Streaming ingest.** Replace the batch generator with a Kafka/Redpanda topic
  and a consumer that handles backpressure, batching, and idempotency.
- **Real attribution modeling.** Multi-touch attribution (last-click vs.
  linear vs. time-decay) instead of the single-touch funnel here.
- **LLM agent.** Swap the rule engine for a model that reads metrics + recent
  performance and proposes actions (with the same guardrails).
- **A SQL interface for the agent.** Let the agent query ClickHouse directly
  through a restricted dialect (whitelisted tables, row limits, timeouts).
- **Observability + load testing.** Prometheus/Grafana, and `k6`/`locust` to
  find where it breaks, then `py-spy` to see why.

Each of those maps directly to a bullet in the job description.
