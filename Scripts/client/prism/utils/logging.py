import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

SLACK_LOGGING_NAMESPACE = "[SLACK | COMMUNITY]"


def setup_logging(log_dir: Path | None, level: int = logging.INFO) -> None:
    base_logger = logging.getLogger(SLACK_LOGGING_NAMESPACE)
    base_logger.setLevel(level)

    # Check to make sure we haven't called "setup_logging" before
    if getattr(base_logger, "_file_handler_installed", False):
        return

    base_logging_dir = (
        Path(log_dir) if log_dir is not None else Path.home() / ".cache" / "Prism-Slack"
    )
    base_logging_dir.mkdir(parents=True, exist_ok=True)
    logging_path = base_logging_dir / "prism_slack_community.log"

    rotating_handler = RotatingFileHandler(
        logging_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    rotating_handler.setFormatter(formatter)

    base_logger.addHandler(rotating_handler)
    base_logger.propagate = (
        False  # Stops duplicates if the root logger somehow got configured
    )

    # Add the guard attribute
    base_logger._file_handler_installed = True


def log_and_print(level: int, message: str) -> None:
    logger = logging.getLogger(SLACK_LOGGING_NAMESPACE)
    logger.log(level, message)
    print(message)
