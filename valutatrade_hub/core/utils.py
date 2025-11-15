import json
import os
import hashlib
from valutatrade_hub.decorators import handle_errors

@handle_errors
def load_data(filepath: str) -> dict | list:
    """ 
    Загружает данные из JSON-файла.
    Если файла не существует или он пуст, 
    -> создает файл с начальными данными (пустой список или словарь).
    """
    if not isinstance(filepath, str):
        raise TypeError('Путь к файлу должен быть представлен строкой.')
    if not os.path.exists(filepath):
        print(f'Файл {filepath} не найден. Создаем новый файл.')
        with open(filepath, mode='w', encoding='utf-8') as f:
            if filepath == 'data/rates.json':
                json.dump({}, f, indent=4, ensure_ascii=False)
                file_content = {}
            else: 
                json.dump([], f, indent=4, ensure_ascii=False)
                file_content = []
        return file_content
    with open(filepath, mode='r', encoding='utf-8') as f:
        file_content = f.read()
        if not file_content:
            with open(filepath, mode='w', encoding='utf-8') as f:
                if filepath == 'data/rates.json':
                    json.dump({}, f, indent=4, ensure_ascii=False)
                    file_content = {}
                else: 
                    json.dump([], f, indent=4, ensure_ascii=False)
                    file_content = []
            return file_content
        else:
            f.seek(0)
            data = json.load(f)
        return data

@handle_errors
def save_data(filepath: str, data: list | dict):
    """
    Сохраняет данные в JSON-файл. 
    """
    if not isinstance(filepath, str):
        raise TypeError('Путь к файлу должен быть строкой.')
    if not isinstance(data, (list, dict)):
        raise TypeError(('Данные для сохранения в JSON-файл '
        f' должны иметь тип списка или словаря.\nПолучен: {type(data)}'))
    
    with open(filepath, mode='w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@handle_errors
def hash_password(password: str, salt: str) -> str:
    """
    Генерирует односторонний псевдо-хеш пароля, используя соль
    """
    if not isinstance(password, str) or not isinstance(salt, str):
        raise TypeError('Пароль и соль должны быть строками.')
    salted_password = (password + salt).encode('utf-8')
    return hashlib.sha256(salted_password).hexdigest()

@handle_errors
def validate_currency_code(currency: str):
    """
    Валидирует код валюты.
    """
    allowed_codes = ['USD', 'RUB', 'EUR', 'BTC', 'ETH', 'SOL']
    if not isinstance(currency, str):
        raise TypeError('Код валюты должен быть строкой.')
    if not currency:
        raise ValueError('Код валюты не может быть пустым.')
    if not currency.isupper():
        raise ValueError(('Код валюты должен быть в верхнем регистре. '
        'Например: "USD", "EUR".'))
    if currency not in allowed_codes:
        raise ValueError((f'Недопустимый код валюты "{currency}".\n '
                          f'Допустимы только: {", ".join(allowed_codes)}'))
    return 'success'
