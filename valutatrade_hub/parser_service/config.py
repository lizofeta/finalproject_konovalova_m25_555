import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass 
class ParserConfig:
    # API ключ для доступа к ExchangeRate 
    load_dotenv(".env")
    EXCHANGE_RATE_API_KEY = os.getenv("API_KEY")

    # Эндпоинты
    COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGE_RATE_URL = "https://v6.exchangerate-api.com/v6"

    # Списки валют
    BASE_CURRENCY = 'USD'
    FIAT_CURRENCIES = ('EUR','RUB', 'USD', 'IRR', 'CNY', 'GBP', 'KZT')
    CRYPTO_CURRENCIES = ('BTC', 'ETH', 'SOL')
    CRYPTO_ID_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    }

    # Пути
    DATA_DIR = Path("data")
    RATES_FILE_PATH = DATA_DIR / "rates.json"
    HISTORY_FILE_PATH = DATA_DIR / "exchange_rates.json"

    # Сетевые параметры
    REQUEST_TIMEOUT = 10 # 10 секунд 