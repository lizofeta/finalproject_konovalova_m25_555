import os
from pathlib import Path

import toml
from dotenv import load_dotenv

from valutatrade_hub.core.exceptions import NoContentError


class SettingsLoader:
    """
    Класс для загрузки и кеширования настроек проекта.
    Реализован как Singleton, чтоб гарантировать единственность экземпляра.
    Способ реализации Singleton-a: 
        метод __new__ ввиду простоты задачи и читабельности подхода.
    """
    _instance = None 
    _config = {} 
    _api_key = None

    def __new__(cls):
        """
        Метод __new__ гарантирует единственность экземпляра класса.
        Если экземпляр еще не был создан - он создается и возвращается.
        Если экземпляр уже был создан - возвращается существующий.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
            cls._instance._load_env()
        return cls._instance
    
    def _load_config(self):
        """
        Загружает конфигурацию из файла pyproject.toml ([tool.valutatrade])
        """
        config_data = {}
        pyproject_filepath = "pyproject.toml"

        try:
            with open(pyproject_filepath, 'r', encoding='utf-8') as f:
                pyproject_content = toml.load(f)
                valtatrade_config = pyproject_content.\
                    get('tool', {}).get('valutatrade', {})
                if valtatrade_config:
                    config_data.update(valtatrade_config)
                else:
                    raise NoContentError(pyproject_filepath)
        except FileNotFoundError:
            print(f'Файл {pyproject_filepath} не найден.')
        except toml.TomlDecodeError as e:
            print(f'Ошибка парсинга файла {pyproject_filepath}: {e}')
        except NoContentError as e:
            print(e)
        
        self.__class__._config = config_data
    
    def _load_env(self):
        env_path = ".env"
        load_dotenv(env_path)
        api_key = os.getenv("API_KEY")
        self.__class__._api_key = api_key

    def get(self, key: str):
        """ Метод для получения значения конфигурации по ключу """
        if not isinstance(key, str):
            raise TypeError('Ключ должен иметь строковый тип')
        if not key.strip():
            raise ValueError('Ключ не должен быть пустым.')
        return self._config.get(key.strip())
    
    def reload(self):
        """ Перезагрузка конфигурации """
        self._load_config()
        self._load_env()
    
    def get_data_dir_path(self):
        """ Метод для получения пути к директории с данными """
        return Path(self.get('data_path'))
    
    def get_users_file_path(self):
        """ Метод для получения пути к файлу пользователей """
        return self.get_data_dir_path() / self.get('users_file_path')
    
    def get_portfolios_file_path(self):
        """ Метод для получения пути к файлу с портфелями """
        return self.get_data_dir_path() / self.get('portfolios_file_path')
    
    def get_rates_file_path(self):
        """ Метод для получения пути к файлу с курсами валют """
        return self.get_data_dir_path() / self.get('rates_file_path')
    
    def get_rates_ttl(self):
        """ Метод для получения времени жизни курсов в секундах """
        return self.get('rates_ttl_seconds')
    
    def get_default_base_currency(self):
        """ Метод для получения базовой валюты по умолчанию """
        return self.get('default_base_currency')
    
    def get_log_info(self):
        """ Метод для получения конфигурации логирования """
        return {
            "log_level": self.get('log_level'),
            "log_format": self.get('log_format')
        }
    
    def get_api_key(self):
        """ Метод для получения ключа API """
        return self._api_key

def get_settings():
    """
    Функция для создания Singleton-а
    """
    return SettingsLoader()