-- =============================================================
-- Postgres = OLTP (transactional / source of truth)
-- Small, mutable, strongly-consistent data:
--   accounts, campaigns, the *decisions* the agent makes, audit log.
-- Nothing here is "big data". If a table would hold billions of
-- rows, it does NOT belong in this database.
-- =============================================================

CREATE TABLE IF NOT EXISTS ad_accounts (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT        NOT NULL,
    vertical        TEXT        NOT NULL,            -- e.g. 'supplements', 'telehealth'
    monthly_budget  NUMERIC(12,2) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS campaigns (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT      NOT NULL REFERENCES ad_accounts(id),
    name            TEXT        NOT NULL,
    channel         TEXT        NOT NULL,            -- 'meta' | 'google' | 'tiktok'
    status          TEXT        NOT NULL DEFAULT 'active', -- active | paused
    daily_budget    NUMERIC(12,2) NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Every budget change the agent makes. This is the audit trail that
-- makes an "agent that spends real money" safe: we can always see
-- what changed, why, and what the world looked like at the time.
CREATE TABLE IF NOT EXISTS agent_actions (
    id              BIGSERIAL PRIMARY KEY,
    campaign_id     BIGINT      NOT NULL REFERENCES campaigns(id),
    action          TEXT        NOT NULL,            -- 'increase' | 'decrease' | 'hold' | 'pause'
    old_budget      NUMERIC(12,2) NOT NULL,
    new_budget      NUMERIC(12,2) NOT NULL,
    reason          TEXT        NOT NULL,
    roas_at_decision NUMERIC(8,4),                   -- the metric the decision was based on
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_campaigns_account ON campaigns(account_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_campaign ON agent_actions(campaign_id, created_at DESC);
