import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_path: str = os.path.join(".", "logs", "collector.log")) -> None:
    """Configura logging rotativo simples em arquivo.

    Cria a pasta de logs se necessário e aplica formatação padrão.
    """
    log_dir = os.path.dirname(log_path) or "."
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Evita adicionar handlers duplicados se já configurado
    if any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        return

    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


