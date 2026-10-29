"""Entry point of the deadline monitor.

Run on a schedule. Each run reads the open orders, assesses every one and, if anything is at risk,
publishes a single digest. It writes nothing to the database, so a retried or duplicated run is harmless.
"""

import logging
import os
from datetime import datetime, timezone
from functools import lru_cache

from deadline_monitor.config import Settings
from deadline_monitor.digest import format_digest
from deadline_monitor.domain import find_risks
from deadline_monitor.notifier import Notifier, SnsNotifier
from deadline_monitor.repository import OrderRepository

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


# Built once per process and reused by later runs of a warm process, which saves the connection
# handshake and client setup; configuration errors surface on the first call, not at import.
@lru_cache(maxsize=1)
def _settings() -> Settings:
    return Settings.from_env()


@lru_cache(maxsize=1)
def _repository() -> OrderRepository:
    return OrderRepository(_settings().database_params())


@lru_cache(maxsize=1)
def _notifier() -> Notifier:
    return SnsNotifier(_settings().alert_topic_arn)


def run(repository: OrderRepository, notifier: Notifier, settings: Settings, now: datetime) -> dict:
    orders = repository.fetch_open_orders()
    risks = find_risks(orders, now, settings.warning_ratio, settings.planning_horizon_days)

    if risks:
        subject, message = format_digest(risks, now)
        notifier.send(subject, message)

    summary = {"checked": len(orders), "at_risk": len(risks), "notified": bool(risks)}
    logger.info("Deadline check finished: %s", summary)
    return summary


def resolve_now(event: dict | None) -> datetime:
    """Use the scheduler's own timestamp when present, so a replayed event gives the same answer."""
    raw = (event or {}).get("time")
    if raw:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def handler(event, context) -> dict:
    return run(_repository(), _notifier(), _settings(), resolve_now(event))
