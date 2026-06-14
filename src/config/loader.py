from logging import getLogger
from yaml import safe_load, YAMLError
from pathlib import Path

from pydantic import ValidationError
from src.config.models import SourcesConfig

logger = getLogger(__name__)

class ConfigLoadError(Exception):
    """Raised when configuration cannot be loaded or validated"""
    pass

def load_sources_config(path: Path) -> SourcesConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = safe_load(f)
    except FileNotFoundError as e:
        logger.error(f"Config file not found: {path}")
        raise ConfigLoadError(f"File not found: {path}") from e
    except YAMLError as e:
        line = e.problem_mark.line + 1 if e.problem_mark else "?"
        logger.error(f"Invalid YAML syntax at line {line}: {e.problem}")
        raise ConfigLoadError(f"Invalid YAML syntax: {e.problem}") from e

    try:
        config = SourcesConfig.model_validate(raw)
        active = sum(1 for s in config.sources.values() if s.enabled)
        logger.info(f"Config loaded: {active}/{len(config.sources)} active source(s)")
        return config
    except ValidationError as e:
        logger.error(f"Config validation failed: {e.error_count()} errors")
        raise ConfigLoadError(f"Validation failed: {e.error_count()} errors") from e