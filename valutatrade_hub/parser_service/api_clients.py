import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import requests

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """
    Абстрактный класс для получения курсов валют.
    Все реализации должны возвращать данные в стандартизированном формате:
    Пример: {'BTC': 59337.27}
    """
    @abstractmethod
    def fetch_rates(self) -> dict:
        pass 

class CoinGeckoClient(BaseApiClient):
    """
    Класс, реализующий получение курсов криптовалют. 

    Возвращает словарь со следующей информацией:
        rate - курс
        updated_at - время обновления курсов
        market_cap - последняя капитализация
    """
    def __init__(self, config: ParserConfig):
        self.config = config
    
    def fetch_rates(self, base:str = None):
        
        ids = ",".join(self.config.CRYPTO_ID_MAP.values())
        if base:
            # Валидация кода валюты
            get_currency(base.upper())
            vs_currencies = base.lower() 
        else:
            vs_currencies = self.config.BASE_CURRENCY.lower()

        params = {
            'ids': ids,
            'vs_currencies': vs_currencies
        }

        try:
            start = time.perf_counter()
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            elapsed_ms = int((time.perf_counter() - start) * 1000)
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko: {str(e)}") from e

        if response.text.strip():
            data = response.json()
        else:
            data = {}
        rates = {}

        for code, name in self.config.CRYPTO_ID_MAP.items():
            pair = f"{code}_{vs_currencies.upper()}"
            try:
                if data:
                    rate_info = data.get(name)
                else:
                    raise ApiRequestError(
                        "CoinGecko: API запрос вернул пустую страницу."
                    )
                if not rate_info:
                    raise ApiRequestError(
                        f'CoinGecko: Нет курса для {code} ({name}).'
                    )
                rate = rate_info.get(vs_currencies.lower())
                updated_at = datetime.now(timezone.utc)\
                    .replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                rates[pair] = {
                     'from_currency': code,
                     'to_currency': vs_currencies.upper(),
                     'rate': float(rate),
                     'timestamp': updated_at,
                     'source': 'CoinGecko',
                     'meta': {
                         'raw_id': name,
                         'request_ms': elapsed_ms,
                         'status_code': response.status_code,
                         'etag': response.headers.get('ETag')
                     }
                 }
            except (TypeError, KeyError) as e:
                raise ApiRequestError(reason=f"CoinGecko: {str(e)}") from e 
        
        return rates 


class ExchangeRateApiClient(BaseApiClient):
    """
    Класс, реализующий получение курсов фиантных валют.

    Возвращает в виде словаря следующую информацию о курсе валют:
        rate - курс
        updated_at - время обновления (отправление запроса к API)
    """
    def __init__(self, config: ParserConfig):
        self.config = config
    
    def fetch_rates(self,base:str = None):
        base_url = self.config.EXCHANGE_RATE_URL
        api_key = self.config.EXCHANGE_RATE_API_KEY
        if not api_key:
            raise ApiRequestError(
                "ExchangeRate-API: Отсутствует API ключ. "
                "Добавьте API_KEY в файл .env"
            )
        if base:
            # Валидация кода валюты
            get_currency(base)
            base_currency = base.upper()
        else:
            base_currency = self.config.BASE_CURRENCY
        

        url = f"{base_url}/{api_key}/latest/{base_currency}"
        currencies = self.config.FIAT_CURRENCIES

        try:
            start = time.perf_counter()
            response = requests.get(
                url, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            elapsed_ms = int((time.perf_counter() - start) * 1000)
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(reason=f"ExchangeRate-API: {str(e)}") from e

        if response.text.strip():
            data = response.json()
        else:
            data = {}

        if not data:
            raise ApiRequestError(
                "ExchangeRate-API: API запрос вернул пустой файл."
            )

        try:
            if data.get('result') != 'success':
                error_type = data.get('error_type', 'неизвестная ошибка')
                raise ApiRequestError(reason=error_type)
            
            rates_data = data.get('conversion_rates')
            if not rates_data:
                raise ApiRequestError(reason='ExchangeRate-API: Курсы недоступны.')
            if not isinstance(rates_data, dict):
                raise ApiRequestError(
                    reason='ExchangeRate-API: Неверная структура ответа API.')

            rates = {}

            for code in currencies:
                pair = f"{code}_{base_currency}"
                rate = rates_data.get(code)
                if not rate:
                    raise ApiRequestError(
                        reason=f"ExchangeRate-API: Нет курса для {code}.")
                updated_at = datetime.now(timezone.utc)\
                        .replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                rates[pair] = {
                    'from_currency': code,
                    'to_currency': base_currency,
                    'rate': rate,
                    'timestamp': updated_at,
                    'source': 'ExchangeRate-API',
                    'meta': {
                        'request_ms': elapsed_ms,
                        'status_code': response.status_code
                    }
                }
        except (KeyError, TypeError) as e:
            raise ApiRequestError(reason=f"ExchangeRate-API: {str(e)}") from e
        
        return rates
