"""The budget agent: read metrics -> decide -> write back (safely).

Rules (deliberately simple for the MVP -- swap in an LLM later):
    roas < target            -> decrease budget (or pause if truly bad)
    target <= roas < scale   -> hold
    roas >= scale            -> increase budget

Every change is clamped and recorded in `agent_actions`, so the whole
loop is auditable and reversible. That audit trail is what makes an
agent that moves real money trustworthy.
"""

from __future__ import annotations

from decimal import Decimal

from .attribution import campaign_roas
from .config import AGENT
from .db import pg_conn


def _decide(roas: float, daily_budget: float) -> tuple[str, float, str]:
    """Return (action, new_budget, reason)."""
    cap = AGENT.max_budget_change_pct

    if roas == 0:
        return "pause", daily_budget, "zero revenue in window; pause pending review"

    if roas < AGENT.target_roas:
        factor = max(0.5, 1 - cap)          # cut, but never more than `cap`
        new_budget = max(50.0, daily_budget * factor)
        return "decrease", round(new_budget, 2), (
            f"roas {roas:.2f} < target {AGENT.target_roas:.2f}; cut budget"
        )

    if roas >= AGENT.scale_roas:
        factor = 1 + cap
        new_budget = daily_budget * factor
        return "increase", round(new_budget, 2), (
            f"roas {roas:.2f} >= scale {AGENT.scale_roas:.2f}; scale budget"
        )

    return "hold", daily_budget, (
        f"roas {roas:.2f} within [{AGENT.target_roas:.2f}, {AGENT.scale_roas:.2f}]; hold"
    )


def run_once(*, dry_run: bool = False) -> list[dict]:
    metrics = {m["campaign_id"]: m for m in campaign_roas()}
    decisions: list[dict] = []

    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, daily_budget FROM campaigns WHERE status = 'active'")
        campaigns = cur.fetchall()

        for camp in campaigns:
            cid = camp["id"]
            budget = float(camp["daily_budget"])
            m = metrics.get(cid)
            roas = float(m["roas"]) if m else 0.0

            action, new_budget, reason = _decide(roas, budget)
            decisions.append(
                {"campaign_id": cid, "action": action,
                 "old_budget": budget, "new_budget": new_budget, "reason": reason}
            )
            if dry_run:
                continue

            if action == "pause":
                cur.execute("UPDATE campaigns SET status='paused', updated_at=now() WHERE id=%s", (cid,))
            elif action in ("increase", "decrease"):
                cur.execute(
                    "UPDATE campaigns SET daily_budget=%s, updated_at=now() WHERE id=%s",
                    (Decimal(str(new_budget)), cid),
                )

            cur.execute(
                """
                INSERT INTO agent_actions
                    (campaign_id, action, old_budget, new_budget, reason, roas_at_decision)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (cid, action, Decimal(str(budget)), Decimal(str(new_budget)), reason, roas),
            )

    return decisions


if __name__ == "__main__":
    import sys

    dry = "--dry-run" in sys.argv
    result = run_once(dry_run=dry)
    changes = [d for d in result if d["action"] != "hold"]
    print(f"Agent evaluated {len(result)} campaigns; {len(changes)} changes "
          f"({'DRY RUN' if dry else 'applied'})")
    for d in changes[:10]:
        print(f"  camp {d['campaign_id']}: {d['action']:>8} "
              f"{d['old_budget']:.0f} -> {d['new_budget']:.0f}  ({d['reason']})")
