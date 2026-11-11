-- =============================================================
-- ClickHouse = OLAP (analytical / high-volume)
-- The event firehose: impressions, clicks, conversions.
-- Append-only, columnar, partitioned by month. This is where the
-- "20 TB/month, billions of rows" workload lives.
-- =============================================================

CREATE DATABASE IF NOT EXISTS converge;

-- ---- Raw event stream ----------------------------------------
-- One row per ad event. Cost is carried on impressions (that's when
-- we pay); revenue is carried on conversions.
CREATE TABLE IF NOT EXISTS converge.events
(
    event_time    DateTime64(3),
    event_date    Date DEFAULT toDate(event_time),
    account_id    UInt64,
    campaign_id   UInt64,
    user_id       UInt64,
    event_type    LowCardinality(String),  -- 'impression' | 'click' | 'conversion'
    cost          Float64 DEFAULT 0,       -- ad spend attributed to this event
    revenue       Float64 DEFAULT 0,       -- conversion value (0 unless conversion)
    impression_id String DEFAULT '',
    click_id      String DEFAULT '',
    conversion_id String DEFAULT ''
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (account_id, campaign_id, event_time);

-- ---- Pre-aggregated daily rollup -----------------------------
-- The core OLAP trick: instead of re-scanning billions of raw rows
-- on every query, we keep a small SummingMergeTree that the DB
-- maintains *incrementally* via a materialized view.
CREATE TABLE IF NOT EXISTS converge.campaign_daily_stats
(
    event_date   Date,
    account_id   UInt64,
    campaign_id  UInt64,
    impressions  UInt64,
    clicks       UInt64,
    conversions  UInt64,
    cost         Float64,
    revenue      Float64
)
ENGINE = SummingMergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, account_id, campaign_id);

-- The materialized view fires on every insert into events and adds
-- its partial aggregates into campaign_daily_stats. This is what
-- keeps a "real-time dashboard over billions of rows" cheap.
CREATE MATERIALIZED VIEW IF NOT EXISTS converge.mv_campaign_daily_stats
TO converge.campaign_daily_stats
AS
SELECT
    toDate(event_time)                              AS event_date,
    account_id,
    campaign_id,
    countIf(event_type = 'impression')              AS impressions,
    countIf(event_type = 'click')                   AS clicks,
    countIf(event_type = 'conversion')              AS conversions,
    sum(cost)                                       AS cost,
    sum(revenue)                                    AS revenue
FROM converge.events
GROUP BY event_date, account_id, campaign_id;
