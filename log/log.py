import os
from typing import Dict, Any
import logging
import yaml
import logging.config

# get logger with configs preset
with open("core/log/config.yaml", "r") as f:
    log_cfg: Dict[str, Any] = yaml.safe_load(f.read())

logging.config.dictConfig(log_cfg)

# Set the logger based on the environment variable
logger_name: str = os.environ.get("LOGGER_NAME", "dev")
logger: logging.Logger = logging.getLogger(logger_name)

# Set the logger level based on the environment variable
logger_level: str = os.environ.get("LOGGER_LEVEL", "DEBUG")
logger.setLevel(logging.getLevelName(logger_level))

# Suppress DEBUG logs for specific libraries project-wide
logging.getLogger("faker").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)
