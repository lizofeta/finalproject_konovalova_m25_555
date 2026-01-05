from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """
    Абстрактный базовый класс для всех валют.

    Атрибуты (public):
        name: str - человекочитаемое имя (например, "US Dollar", "Bitcoin").
        code: str - ISO-код или общепринятый тикер ("USD", "EUR", "BTC", "ETH").
    
    Методы:
        get_display_info() -> str - строковое представление для UI/логов.
    
    Инварианты: 
        code - верхний регистр, 2-5 символов, без пробелов.
        name - не пустая строка.
    """
    def __init__(self, name:str, code:str):
        if not isinstance(name, str):
            raise TypeError('Название валюты должно быть строкой.')
        if not name.strip():
            raise ValueError('Название валюты не должно быть непустым.')
        self.name = name 
        if not isinstance(code, str):
            raise TypeError('Код валюты должен быть строкой.')
        if ' ' in code.strip():
            raise ValueError('Код валюты не должен содержать пробелов.')
        if code != code.upper():
            raise ValueError(f'Код валюты должен быть записан в \
                             верхнем регистре, например: {code.upper()}')
        self.code = code 
    
    @abstractmethod
    def get_display_info(self) -> str:
        """
        Возвращает строковое представление для UI/логов с информацией о валюте.
        """
        pass

class FiatCurrency(Currency):
    """
    Класс фиатных валют (национальных), наследуется от абстректного класса Currency.

    Дополнительный атрибут: 
        issuing_country: str (например, “United States”, “Eurozone”).

    Переопределение: 
        get_display_info() (добавляет страну/зону эмиссии).
    """
    def __init__(self, name, code, issuing_country):
        """
        Инициализирует объект фиатной валюты.

        Аргументы:
            name: str - человекочитаемое имя (например, "US Dollar", "Bitcoin").
            code: str - ISO-код или общепринятый тикер ("USD", "EUR", "BTC", "ETH").
            issuing_country: str - страна или зона эмиссии (например, “United States”).
        """
        super().__init__(name, code)
        if not isinstance(issuing_country, str):
            raise TypeError('Страна эмиссии должна быть строкой.')
        if not issuing_country.strip():
            raise ValueError('Страна эмиссии не должна быть пустой.')
        self.issuing_country = issuing_country
    
    def get_display_info(self):
        return f"[FIAT] {self.code} - {self.name} (Issuing: {self.issuing_country})"
    

class CryptoCurrency(Currency):
    """
    Класс криптовалют, наследуется от абстректного класса Currency.

    Дополнительные атрибуты:
        algorithm: str (например, “SHA-256”, “Ethash”), 
        market_cap: float (последняя известная капитализация).
    
    Переопределение:
         get_display_info() (алгоритм + краткая капитализация).
    """
    def __init__(self, name, code, algorithm:str, market_cap:float|int):
        """
        Инициализирует объект криптовалюты.

        Аргументы:
            name: str - человекочитаемое имя (например, "US Dollar", "Bitcoin").
            code: str - ISO-код или общепринятый тикер ("USD", "EUR", "BTC", "ETH").
            algorithm: str - алгоритм хеширования (например, “SHA-256”, “Ethash”), 
            market_cap: float - последняя известная капитализация (в долларах).
        """
        super().__init__(name, code)
        if not isinstance(algorithm, str):
            raise TypeError('Алгоритм хеширования должен быть строкой.')
        if not algorithm.strip():
            raise ValueError('Алгоритм хеширования не должен быть пустым.')
        self.algorithm = algorithm.strip()

        if not isinstance(market_cap, float|int):
            raise TypeError('Рыночная капитализация должна быть числом.')
        self.market_cap = market_cap
    
    def update_market_cap(self, market_cap:float|int):
        """ Метод для обновления информации о последней рыночной капитализации """
        if not isinstance(market_cap, float|int):
            raise TypeError('Рыночная капитализация должна быть числом ')
        self.market_cap = market_cap
    
    def get_display_info(self):
        return f"[CRYPTO] {self.code} - {self.name}\
              (Algo: {self.algorithm}, MCAP: {self.market_cap})"

# Реестр валют
_CURRENCY_REGISTRY  = {}

def register_currency(currency: Currency):
    """
    Заносит валюту в глобальный реестр валют
    """
    _CURRENCY_REGISTRY[currency.code] = currency 

def get_currency(code: str) -> Currency:
    """
    Получает валюту из реестра по коду.
    """
    code = code.upper()
    if code in _CURRENCY_REGISTRY:
        return _CURRENCY_REGISTRY.get(code)
    else:
        raise CurrencyNotFoundError(code)

def initialize_currencies():
    """ Инициализирует реестр валют """
    # Фиатные валюты
    register_currency(FiatCurrency('US Dollar', 'USD', 'Unated States'))
    register_currency(FiatCurrency('Euro', 'EUR', 'Eurozone'))
    register_currency(FiatCurrency('Ruble', 'RUB', 'Russian Federation'))
    register_currency(FiatCurrency('Rial', 'IRR', 'Iran'))
    
    # Криптовалюты
    register_currency(CryptoCurrency('Bitcoin', 'BTC', 'SHA-256', 1823276180070))
    register_currency(CryptoCurrency('Ethereum', 'ETH', 'Ethash', 379346713823))
    register_currency(CryptoCurrency('Solana', 'SOL', 'Proof of History', 75705339051))

def get_all_currencies():
    """ Возвращает доступные валюты в виде словаря """
    return _CURRENCY_REGISTRY.copy()