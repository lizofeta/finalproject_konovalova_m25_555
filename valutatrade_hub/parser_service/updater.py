import logging
from datetime import datetime, timezone

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import ApiRequestError

from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig
from .storage import HistoryStorage, RatesStorage

logger = logging.getLogger('valutatrade_hub.parser.updater')

class RatesUpdater:
    def __init__(self, config: ParserConfig):
        self.config = config 
        self.clients = {
            'coingecko': CoinGeckoClient(config),
            'exchangerate': ExchangeRateApiClient(config)
        }
        self.history = HistoryStorage(config)
        self.cache = RatesStorage(config)
    
    def run_update(self, source:str = None, base:str = None):
        if source:
            source = source.lower()
        if base:
            # Валидация кода валюты
            get_currency(base)
            base_currency = base.upper() 
        else:
            base_currency = self.config.BASE_CURRENCY

        logger.info('Запускаем обновление курсов...')
        history_records = []
        cache_snapshot = {}
        last_updated = datetime.now(timezone.utc)\
            .isoformat().replace('T', ' ').replace('+00:00', '')
        # Получаем данные
        for name, client in self.clients.items():
            if source and name != source:
                continue
            try:
                data = client.fetch_rates(base=base_currency)
                logger.info(f"Извлечено {len(data)} курсов из {name}.")

                for pair, rates in data.items():
                    record_id = f"{pair}_{rates.get('timestamp')}"
                    history_records.append({'id': record_id, **rates})
                    cache_snapshot[pair] = {
                        "rate": rates.get('rate'),
                        "updated_at": rates.get('timestamp'),
                        "source": rates.get('source')
                    }
            except Exception as e:
                logger.exception(f'Произошла ошибка извлечения курсов из {name}: {e}')
                raise ApiRequestError from e
        if history_records:
            self.history.append(history_records)
        if cache_snapshot:
            logger.info((f"Сохраняем {len(cache_snapshot)} курсов "
                         f"в {self.config.RATES_FILE_PATH}"))
            self.cache.save_rates(cache_snapshot)
        
        logger.info(f"Обновление курсов завершено успешно. "
                    f" Всего обновлено: {len(cache_snapshot)} курсов. "
                    f" Последнее обновление: {last_updated}")