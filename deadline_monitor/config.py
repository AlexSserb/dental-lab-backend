"""Settings, read once from environment variables.

Required: DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST, ALERT_TOPIC_ARN
Optional: DATABASE_PORT (5432), DEADLINE_WARNING_RATIO (0.8), DEADLINE_PLANNING_HORIZON_DAYS (3), LOG_LEVEL (INFO)
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass


class ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    database_name: str
    database_user: str
    database_password: str
    database_host: str
    database_port: int
    alert_topic_arn: str
    warning_ratio: float
    planning_horizon_days: int

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if env is None else env
        required = ("DATABASE_NAME", "DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_HOST", "ALERT_TOPIC_ARN")
        missing = [name for name in required if not env.get(name)]
        if missing:
            raise ConfigurationError(f"Missing environment variables: {', '.join(missing)}")

        warning_ratio = float(env.get("DEADLINE_WARNING_RATIO", "0.8"))
        if not 0 < warning_ratio <= 1:
            raise ConfigurationError("DEADLINE_WARNING_RATIO must be in (0, 1]")

        return cls(
            database_name=env["DATABASE_NAME"],
            database_user=env["DATABASE_USER"],
            database_password=env["DATABASE_PASSWORD"],
            database_host=env["DATABASE_HOST"],
            database_port=int(env.get("DATABASE_PORT", "5432")),
            alert_topic_arn=env["ALERT_TOPIC_ARN"],
            warning_ratio=warning_ratio,
            planning_horizon_days=int(env.get("DEADLINE_PLANNING_HORIZON_DAYS", "3")),
        )

    def database_params(self) -> dict[str, str | int]:
        return {
            "dbname": self.database_name,
            "user": self.database_user,
            "password": self.database_password,
            "host": self.database_host,
            "port": self.database_port,
            "connect_timeout": 5,
            "options": "-c statement_timeout=10000",
        }
