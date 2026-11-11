"""Central configuration, read from environment (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _int(key: str, default: int) -> int:
    return int(os.getenv(key, default))


def _float(key: str, default: float) -> float:
    return float(os.getenv(key, default))


@dataclass(frozen=True)
class PgConfig:
    host: str = os.getenv("PG_HOST", "localhost")
    port: int = _int("PG_PORT", 5432)
    user: str = os.getenv("PG_USER", "converge")
    password: str = os.getenv("PG_PASSWORD", "converge")
    db: str = os.getenv("PG_DB", "converge")

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} user={self.user} "
            f"password={self.password} dbname={self.db}"
        )


@dataclass(frozen=True)
class ChConfig:
    host: str = os.getenv("CH_HOST", "localhost")
    port: int = _int("CH_PORT", 8123)
    user: str = os.getenv("CH_USER", "converge")
    password: str = os.getenv("CH_PASSWORD", "converge")
    db: str = os.getenv("CH_DB", "converge")


@dataclass(frozen=True)
class SimConfig:
    days: int = _int("SIM_DAYS", 7)
    accounts: int = _int("SIM_ACCOUNTS", 5)
    campaigns_per_account: int = _int("SIM_CAMPAIGNS_PER_ACCOUNT", 8)
    impressions_per_day: int = _int("SIM_IMPRESSIONS_PER_DAY", 5000)
    seed: int = _int("SIM_SEED", 42)


@dataclass(frozen=True)
class AgentConfig:
    target_roas: float = _float("AGENT_TARGET_ROAS", 2.0)
    scale_roas: float = _float("AGENT_SCALE_ROAS", 4.0)
    max_budget_change_pct: float = _float("AGENT_MAX_BUDGET_CHANGE_PCT", 0.30)
    lookback_days: int = _int("AGENT_LOOKBACK_DAYS", 7)


PG = PgConfig()
CH = ChConfig()
SIM = SimConfig()
AGENT = AgentConfig()
