import json
import os
from datetime import datetime
from pathlib import Path

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.infra.settings import get_settings


class DatabaseManager():
    """
    Класс для управления базой данных
    Предназначен для:
     - загрузки данных с JSON-файлов
     - сохранения новой информации на JSON-файлы
    """
    def __init__(self):
        settings = get_settings()
        self.dir_data_path = settings.get_data_dir_path()
        os.makedirs(self.dir_data_path, exist_ok=True)
        self.users_file_path = settings.get_users_file_path()
        self.portfolios_file_path = settings.get_portfolios_file_path()
        self.rates_file_path = settings.get_rates_file_path()

        self.users_data = None 
        self.portfolios_data = None
        self.rates_data = None 
    
    def _load_json(self, filepath: Path):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return [] if filepath.name in ['users.json', 'portfolios.json'] else {}
    
    def _save_json(self, filepath: Path, data: dict | list):
        """ Метод для загрузки данных из JSON-файла """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(('Произошла непредвиденная ошибка '
                   f'при загрузке данных в файл {filepath}: {e}'))
    
    def load_users(self) -> list[User]:
        """ Метод для загрузки содержания файла пользователей """
        self.users_data = self._load_json(self.users_file_path)
        return [User.from_dict(user) for user in self.users_data]
    
    def save_users(self, users: list[User]):
        """ Метод для сохранения данных о пользователях в файл JSON """
        self.users_data = [User.to_dict(user) for user in users]
        self._save_json(self.users_file_path, self.users_data)
    
    def find_user_by_username(self, username: str):
        """ Метод для поиска пользователя по его имени """
        users = self.load_users()
        for user in users:
            if user.username == username:
                return user
        return None
    
    def find_user_by_id(self, user_id: int):
        """ Метод для поиска пользователя по его ID """
        users = self.load_users()
        for user in users:
            if user.user_id == user_id:
                return user 
        return None

    def load_portfolios(self) -> list[Portfolio]:
        """ Метод для загрузки содержания файла портфелей """
        self.portfolios_data = self._load_json(self.portfolios_file_path)
        return [Portfolio.from_dict(portfolio) for portfolio in self.portfolios_data]
    
    def save_portfolios(self, portfolios: list[Portfolio]):
        """ Метод для сохранения данных портфелей в JSON-файл """
        self.portfolios_data = [Portfolio.to_dict(portfolio)\
                                 for portfolio in portfolios]
        self._save_json(self.portfolios_file_path, self.portfolios_data)
    
    def find_portfolio_by_user_id(self, user_id: int):
        """ Метод для поиска портфеля пользователя по его ID """
        portfolios = self.load_portfolios()
        for portfolio in portfolios:
            if portfolio.user_id == user_id:
                return portfolio 
        return None
    
    def save_portfolio(self, portfolio:Portfolio):
        """ Метод для сохранения (обновления или создания) портфеля """
        portfolios = self.load_portfolios()
        exists = False
        for i, p in enumerate(portfolios):
            if p._user_id == portfolio._user_id:
                portfolios[i] = portfolio 
                exists = True
                break 
        
        if not exists:
            portfolios.append(portfolio)
        
        self.save_portfolios(portfolios)

    
    def load_rates(self):
        """ Метод для загрузки данных о курсах валют """
        self.rates_data = self._load_json(self.rates_file_path)

        if not isinstance(self.rates_data, dict):
            return {'rates': {}, 'last_refresh': None}
        
        return self.rates_data
    
    def save_rates(self, data: dict):
        """ Метод для схранения данных о курсах валют в файл JSON """
        self.rate_data = {
            'rates': data.get('rates', {}),
            'last_refresh': data.get('last_refresh')
        }
        self._save_json(self.rates_file_path, self.rates_data)

    def get_rate(self, from_currency: str, to_currency: str):
        """ 
        Метод для получения курса для пары валют:

        - from_currency: Исходная валюта
        - to_currency: Целевая валюта
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        self.rates_data = self.load_rates()
        rates = self.rates_data.get('rates')
        
        rate_key_direct = f'{from_currency}_{to_currency}'
        if rate_key_direct in rates:
            return rates.get(rate_key_direct)
        
        rate_key_reverse = f'{to_currency}_{from_currency}'
        if rate_key_reverse in rates:
            return 1 / rates.get(rate_key_reverse)
        
        return None
    
    def update_rate(self, from_currency: str, to_currency: str, rate: float):
        """ Метод для обновления курса валют """
        self.rate_data = self.load_rates()
        codes = self.rates_data.setdefault('codes', {})
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        rate_key = f'{from_currency}_{to_currency}'
        codes[rate_key] = {
            "rate": rate,
            "updated_at": datetime.now().isoformat()
        }
        self.save_rates(self.rate_data)


# Гарантия единственности экземпляра 
_database = None

def get_database():
    """ Функция для создания экземпляра менеджера БД """
    global _database
    if _database is None:
        _database = DatabaseManager()
    return _database