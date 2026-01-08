import logging
import threading
import time

from valutatrade_hub.core.exceptions import ApiRequestError

from .updater import RatesUpdater

logger = logging.getLogger('valutatrade_hub.parser.scheduler')

class RatesScheduler:
    """
    Планировщик периодического обновления курсов.
    Запускает RatesUpdater.run_update() с заданным интервалом.
    """
    def __init__(
            self, 
            updater: RatesUpdater, 
            time_interval: int, 
            source: str = None
        ):
        self.updater = updater
        self.time_interval = time_interval
        self.source = source

        self._stop_event = threading.Event()
        self._thread = None 
    
    def _run_scheduled_updater(self):
        """
        Основной цикл планировщика обновления курсов.
        """
        while not self._stop_event.is_set():
            start_time = time.time()
            try:
                logger.info("Запуск автоматического обновления курсов."
                            f" Источник: {self.source or 'все'}")
                self.updater.run_update(self.source)
                logger.info("Автообновление курсов успешно завершено.")
            except ApiRequestError as e:
                logger.error(f"Произошла ошибка автообновления курсов: {e}")
            except Exception:
                logger.exception(("Произошла непредвиденная ошибка "
                        "во время автоматического обновления курсов."))
            elapsed = time.time() - start_time 
            sleep_time = max(0, self.time_interval - elapsed)
            logger.debug(f"Следующее обновление через {sleep_time} сек.")
            self._stop_event.wait(timeout=sleep_time)
    
    def start(self):
        """
        Метод для запуска планировщика в отдельном потоке.
        """
        if self._thread and self._thread.is_alive():
            logger.warning("Обновление в процессе выполнения.")
            return 
        
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_scheduled_updater,
            name="RatesSchedulerThread",
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """
        Остановка планировщика.
        """
        logger.info("Остановка автообновления курсов.")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            logger.info("Автообновление курсов остановлено.")