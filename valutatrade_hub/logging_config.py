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
    log_dir.mkdir(exist_ok=True)

    # Путь к файлу логирования 
    log_file_path = log_dir / "actions.log"

    # Информация для настройки формата логирования 
    log_cfg = settings.get_log_info()
    log_format = log_cfg.get('log_format') 
    date_format = log_cfg.get('date_format')

    root_logger = logging.getLogger()

    # Проверка, настроено ли уже логирование
    if root_logger.handlers:
        return 
    
    # Настройка ротации
    handler = RotatingFileHandler(
        log_file_path,
        maxBytes=5*1024*1024,
        backupCount=10,
        encoding='utf-8'
    )

    # Формат
    formatter = logging.Formatter(
        fmt=log_format,
        datefmt=date_format
    )

    handler.setFormatter(formatter)
    root_logger.setLevel(level)
    root_logger.addHandler(handler)