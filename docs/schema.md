# Data model

The single most important decision in this project is **which data lives in
which database**. That choice is what makes the platform able to handle
"billions of rows in real time" without falling over.

## The rule of thumb

| Property | Postgres (OLTP) | ClickHouse (OLAP) |
|---|---|---|
| Row count | thousands – millions | billions – trillions |
| Writes | frequent small updates | append-only, in huge batches |
| Reads | point lookups by key | scans + aggregations over columns |
| Consistency | strong (transactions) | eventual, but blazing fast |
| What breaks it | huge tables, scan-heavy queries | row-level updates, many small writes |

If a table would hold billions of rows, it does **not** belong in Postgres.
If a table needs `UPDATE ... WHERE id = ...`, it does **not** belong in
ClickHouse.

## Postgres (OLTP) — the small, mutable, authoritative state

### `ad_accounts`
The brands we buy ads for. Small, changes rarely.

| column | type | notes |
|---|---|---|
| id | bigserial | PK |
| name | text | brand name |
| vertical | text | supplements / telehealth / ... |
| monthly_budget | numeric | the account-level cap |
| created_at | timestamptz | |

### `campaigns`
One row per ad campaign. `daily_budget` is the column the agent mutates.

| column | type | notes |
|---|---|---|
| id | bigserial | PK |
| account_id | bigint | FK -> ad_accounts |
| name | text | |
| channel | text | meta / google / tiktok |
| status | text | active / paused |
| daily_budget | numeric | **the agent's lever** |
| updated_at | timestamptz | |

### `agent_actions` — the audit trail
Every decision the agent makes, forever. This is what makes an agent that
spends real money *safe*: you can always answer "what changed, why, and what
did the world look like at the time?"

| column | type | notes |
|---|---|---|
| id | bigserial | PK |
| campaign_id | bigint | FK -> campaigns |
| action | text | increase / decrease / hold / pause |
| old_budget | numeric | |
| new_budget | numeric | |
| reason | text | human-readable justification |
| roas_at_decision | numeric | the metric the decision was based on |
| created_at | timestamptz | |

## ClickHouse (OLAP) — the high-volume event firehose

### `events`
One row per ad event. Append-only, columnar, partitioned by month.
This is where the "20 TB/month" workload lives.

| column | type | notes |
|---|---|---|
| event_time | DateTime64(3) | |
| event_date | Date | partition key (derived) |
| account_id | UInt64 | |
| campaign_id | UInt64 | |
| user_id | UInt64 | |
| event_type | LowCardinality(String) | impression / click / conversion |
| cost | Float64 | ad spend (on impressions — that's when we pay) |
| revenue | Float64 | conversion value (on conversions) |
| impression_id / click_id / conversion_id | String | for join-back / dedup |

**Engine:** `MergeTree`, `PARTITION BY toYYYYMM(event_date)`,
`ORDER BY (account_id, campaign_id, event_time)`.

### `campaign_daily_stats` + `mv_campaign_daily_stats`
The pre-aggregated rollup. Instead of scanning billions of raw rows on every
query, we keep a tiny `SummingMergeTree` that ClickHouse maintains
*incrementally* via a materialized view.

| column | type |
|---|---|
| event_date | Date |
| account_id | UInt64 |
| campaign_id | UInt64 |
| impressions | UInt64 |
| clicks | UInt64 |
| conversions | UInt64 |
| cost | Float64 |
| revenue | Float64 |

The materialized view (`mv_campaign_daily_stats`) fires on every insert into
`events` and adds partial aggregates into this table.

### Why a `SummingMergeTree`?
The engine knows how to *sum* rows that share the same sort key. So a query
just sums the (already-partially-summed) rows and gets the right answer without
touching raw events. This is the single biggest lever for keeping a
"real-time dashboard over billions of rows" cheap.

### Gotcha: truncating the source does not clear the rollup
The materialized view only fires on *inserts*. `TRUNCATE events` leaves
`campaign_daily_stats` untouched, so re-runs would double-count. The generator
truncates both tables explicitly. This is exactly the kind of subtle bug that
bites in production OLAP pipelines.

## The metric

**ROAS** (Return On Ad Spend) = `revenue / cost`, over a rolling window.
The agent compares it against two thresholds:

- `roas < target` (default 2.0) → decrease budget
- `target <= roas < scale` (default 4.0) → hold
- `roas >= scale` → increase budget

Budget changes are clamped to ±`AGENT_MAX_BUDGET_CHANGE_PCT` (default 30%) so
the agent can never swing a budget wildly on one noisy reading.
