"""Seed the OLTP side (Postgres): ad accounts and campaigns.

These are the *small, mutable* entities the platform actually owns.
Real money decisions point back at these rows, so they live in a
transactional database with foreign keys and an audit trail.
"""

from __future__ import annotations

import random

from faker import Faker

from .config import SIM
from .db import pg_conn

VERTICALS = ["supplements", "telehealth", "skincare", "apparel", "pet_food"]
CHANNELS = ["meta", "google", "tiktok"]


def seed_postgres() -> None:
    fake = Faker()
    Faker.seed(SIM.seed)
    rng = random.Random(SIM.seed)

    with pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE agent_actions, campaigns, ad_accounts RESTART IDENTITY CASCADE")

            account_ids: list[int] = []
            for _ in range(SIM.accounts):
                cur.execute(
                    """
                    INSERT INTO ad_accounts (name, vertical, monthly_budget)
                    VALUES (%s, %s, %s) RETURNING id
                    """,
                    (
                        fake.company(),
                        rng.choice(VERTICALS),
                        round(rng.uniform(50_000, 500_000), 2),
                    ),
                )
                account_ids.append(cur.fetchone()["id"])

            for account_id in account_ids:
                for c in range(SIM.campaigns_per_account):
                    cur.execute(
                        """
                        INSERT INTO campaigns (account_id, name, channel, daily_budget)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            account_id,
                            f"{rng.choice(CHANNELS)}_camp_{c}_{fake.word()}",
                            rng.choice(CHANNELS),
                            round(rng.uniform(200, 5_000), 2),
                        ),
                    )

    print(f"Postgres seeded: {SIM.accounts} accounts, "
          f"{SIM.accounts * SIM.campaigns_per_account} campaigns")


if __name__ == "__main__":
    seed_postgres()
