import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from valutatrade_hub.infra.settings import get_settings


def setup_logging(level=logging.INFO):
    """
    Функция настройки логирования
    """
    settings = get_settings()

    # Создадим директорию для лог-файлов
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Информация для настройки формата логирования 
    log_cfg = settings.get_log_info()
    log_format = log_cfg.get('log_format') 
    date_format = log_cfg.get('date_format')

    root_logger = logging.getLogger()

    # Формат
    formatter = logging.Formatter(
        fmt=log_format,
        datefmt=date_format
    )

    # Core:
    if not root_logger.handlers:
        # Настройка хендлера
        core_handler = RotatingFileHandler(
            log_dir / "actions.log",
            maxBytes=5*1024*1024,
            backupCount=10,
            encoding='utf-8'
        )

        core_handler.setFormatter(formatter)
        root_logger.setLevel(level)
        root_logger.addHandler(core_handler)

    # Parser:
    parser_logger = logging.getLogger('valutatrade_hub.parser')

    if not parser_logger.handlers:
        # Настройка хендлеров
        parser_handler = RotatingFileHandler(
            log_dir / "parser.log",
            maxBytes=5*1024*1024,
            backupCount=10,
            encoding='utf-8'
        )
        parser_handler.setFormatter(formatter)
        parser_handler.setLevel(logging.DEBUG)
        parser_logger.setLevel(logging.DEBUG)
        parser_logger.addHandler(parser_handler)
        parser_logger.propagate = False