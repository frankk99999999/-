# How this differs from real Converge

This is a **learning reproduction of the architecture**, not a clone of the
product. This document is deliberately blunt about the gap, because knowing
where you are is the whole point of the exercise.

Everything below about "real Converge" comes from their public job posting
(Founding Platform Engineer, NYC). Treat those numbers as *their claims*, not
as facts I have verified — you should re-read the posting yourself and correct
this file as you learn more.

---

## The gap, in one table

| Dimension | This repo | Real Converge |
|---|---|---|
| Scale of events | ~5.7M events/run, ~215k/s ingest | **20 TB/month**, ~10k jobs/s peak, "trillion jobs/month" target |
| Revenue touched | simulated $ | **$6B annual revenue**, $1M+ daily budgets |
| Customers | 0 (synthetic) | **200+**, incl. Hims & Hers |
| Data sources | fake generator | **real ad-platform APIs** (Meta, Google, TikTok) |
| Attribution | single-touch funnel, pre-aggregated daily rollup | multi-touch attribution over **billions of rows joined in real time** |
| The agent | **rule-based** (thresholds on ROAS) | **ML/LLM agent** that learns from results and produces new ad creative |
| Budget changes | clamped ±30%, audited | **>90% of all budget changes**, automated |
| Agent query interface | none (fixed SQL in Python) | a **SQL dialect** the agent queries directly |
| Infra | one Docker Compose, one machine | distributed services, ClickHouse at scale, flamegraph-level tuning |
| Team | you | 13 people, 3 product engineers, you'd be first platform engineer |
| Team size that built this | 1 | 13 (and they've raised $5.7M) |

---

## What is *faithful* (the parts worth learning from)

These are the ideas that transfer directly to the real system:

1. **OLTP/OLAP split.** Real Converge uses Postgres **and** ClickHouse. So do we,
   for the same reason: small mutable state vs. a high-volume columnar firehose.
2. **Materialized aggregation.** The "materialize our attribution dataset to scale
   joining and aggregating billions of rows in realtime" bullet is the core
   problem. We reproduce the *shape* of the solution: a `SummingMergeTree` fed
   by a materialized view, and we *measure* the win (raw scan vs. rollup).
3. **Batched, append-only ingest.** We insert in 20k-row batches and never hold
   the dataset in memory — the same discipline a real 10k jobs/s ingester needs.
4. **An agent with a write-back path and an audit trail.** The agent's whole job
   is to change budgets safely and explainably. We reproduce the safety
   scaffolding (clamping, reasons, immutable action log) even though the decision
   logic itself is trivial.
5. **The metrics are real.** ROAS, cost, revenue, the impression→click→conversion
   funnel, CPM-based billing — these are the actual quantities ad platforms care
   about.

## What is *not* faithful (and why it matters)

### 1. The agent is a rule engine, not a learning agent
Real Converge's agents "learn from results and produce new ads to close the
loop." Ours compares ROAS to two fixed thresholds. This is the single biggest
gap. It's also the easiest to close incrementally — see "Next steps."

### 2. No streaming
We generate and bulk-load. Real Converge ingests continuously with backpressure
and job orchestration. Batch hides the hardest part: what happens when the
firehose is *live* and never stops.

### 3. Attribution is a toy
We do single-touch, and we don't even do the join in real time — we pre-aggregate
daily. Real Converge joins conversion data against spend across **billions of
rows, in real time**, which is why they stare at ClickHouse flamegraphs. Our
`attribution.py` is a sketch of the problem, not a solution to it.

### 4. Scale is off by ~4-5 orders of magnitude
5.7M events vs. 20 TB/month. The *techniques* are the same; the *failure modes*
are not. At their scale, the interesting bugs are in sharding, replication,
memory pressure, and query planning — none of which appear at our size.

### 5. No ad-platform integration
No Meta/Google/TikTok APIs, no OAuth, no rate limits, no retries against a
flaky third party. In reality, "the API returned a 429 at 3am" is half the job.

### 6. No query interface for the agent
They're building a SQL dialect so agents can query data directly. We hardcode
SQL in Python. Giving the agent a constrained query surface (whitelisted tables,
row limits, timeouts, permissions) is a real, hard, security-relevant project.

### 7. Single machine, no orchestration
One Compose file. No Kubernetes, no queue, no scheduler, no service mesh, no
observability stack. And no `py-spy` flamegraphs — which they explicitly
mention, so you should go generate some.

---

## How to use this document

Do not present this repo as "I cloned Converge." Present it as:

> "I read Converge's platform-engineering job description, extracted the hard
> problems it names, and built a small system that exercises each one. Here's
> what I learned about the OLTP/OLAP split and materialized attribution, and
> here's the honest list of what I *didn't* build."

Then pick **one** item from "not faithful" and close it properly. That — not
breadth — is what makes this credible in an interview.

## Suggested order to close the gaps

1. **Streaming ingest** (Redpanda + a consumer with idempotency & backpressure).
   Biggest conceptual jump, most transferable to the real job.
2. **Real-time multi-touch attribution** over a large synthetic dataset.
   Directly mirrors their headline infra problem.
3. **LLM agent** with guardrails + offline evaluation of its decisions.
4. **Restricted SQL interface** for the agent.
5. **Observability + load test**, then `py-spy` flamegraphs on the hot path.
