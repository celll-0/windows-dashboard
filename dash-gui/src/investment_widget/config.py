"""Runtime configuration, persisted as ``config.yml`` at the project root."""
from __future__ import annotations

import yaml
from dataclasses import dataclass, asdict
from loguru import logger

from .paths import CONFIG_PATH


@dataclass
class Config:
    base_url: str
    poll_interval_seconds: int
    position: dict
    timezone: str

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from the project root, or create a default if not found."""
        conf = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        cfg = cls(
            base_url=conf["base_url"],
            timezone=conf["timezone"],
            poll_interval_seconds=int(conf["poll_interval_seconds"]),
            position=conf["position"],
        )
        logger.info(
            "Config loaded | base_url={} poll_interval={}s position={}",
            cfg.base_url,
            cfg.poll_interval_seconds,
            cfg.position,
        )
        return cfg

    def save(self) -> None:
        CONFIG_PATH.write_text(yaml.dump(asdict(self), default_flow_style=False), encoding="utf-8")
        logger.debug("Config saved to {}", CONFIG_PATH)