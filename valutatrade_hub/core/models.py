import datetime
import hashlib
import uuid
import requests 
from valutatrade_hub.core.constants import (
    BASE_URL_EXCHANGE_RATE,
    API_KEY
)

class User:

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """
        Генерирует односторонний псевдо=хеш пароля, используя соль
        """
        if not isinstance(password, str) or not isinstance(salt, str):
            raise TypeError('Пароль и соль должны быть строками.')
        salted_password = (password + salt).encode('utf-8')
        return hashlib.sha256(salted_password).hexdigest()


    def __init__(
            self, 
            user_id: int, 
            username: str, 
            hashed_password: str, 
            salt: str, 
            registration_date: datetime
        ): 
        """
        Конструктор класса User

        user_id: уникальный идентификатор пользователя
        username: имя пользователя
        hashed_password: пароль в зашифрованном виде
        salt: уникальная соль для пользователя
        registration_date: дата регистрации пользователя
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError('Уникальный идентификатор должен быть целым положительным числом.')
        self._user_id = user_id
        
        self._username = username 

        if not isinstance(hashed_password, str):
            raise TypeError('Хешированный пароль болжен быть представлен строкой.')
        if len(hashed_password.strip()) < 4:
            raise ValueError('Пароль должен быть не короче 4 символов.')
        self._hashed_password = hashed_password 

        if not isinstance(salt, str):
            raise TypeError('Соль должна быть представленна строкой.')
        self._salt = salt 

        if not isinstance(registration_date, datetime.datetime):
            raise TypeError('Дата регистрации должна быть объектом datetime')
        self._registration_date = registration_date 

    @property
    def user_id(self):
        return self._user_id
    
    @property
    def username(self):
        return self._username 
    
    @username.setter
    def username(self, value: str):
        if not isinstance(value, str):
            raise TypeError('Имя должно быть представленно строкой.')
        if not value.strip():
            raise ValueError('Имя не должно быть пустым.')
        self._username = value.strip()
    
    @property
    def hashed_password(self):
        return self._hashed_password
    
    @property
    def salt(self):
        return self._salt 
    
    @property
    def registration_date(self):
        return self._registration_date
    
    def get_user_info(self):
        """Возвращает информацию о пользователе"""
        return {
            'user_id': self._user_id,
            'username': self._username,
            'hashed_password': self._hashed_password,
            'salt': self._salt,
            'registration_date': self._registration_date.isoformat()
        }
    
    def change_password(self, new_password: str):
        """
        Изменяет пароль пользователя, хешируя новый пароль с новой солью.
        """
        if len(new_password.strip()) < 4:
            raise ValueError('Пароль должен быть не короче 4 символов.')
        new_salt = uuid.uuid4.hex()
        self._salt = new_salt 
        self._hashed_password = self._hash_password(new_password, new_salt)
        return self._hashed_password

    def verufy_password(self, password):
        """
        Проверяет введенный пользователем пароль на совпадение с сохраненным 
        хешированнвм паролем.
        """
        if not isinstance(password, str):
            return False
        password_to_verify = self._hash_password(password, self._salt)
        return password_to_verify == self._hashed_password


class Wallet:
    """
    Класс кошелька пользователя для одной конкретной валюты
    """
    def __init__(
            self, 
            currency_code: str,
            balance=0.0
        ):
        """
        Конструктор класса кошелька

        currency_code: код валюты, например "USD", "BTC"
        balance: баланс в данной валюте. По умолчанию = 0.0
        """
        if not isinstance(currency_code, str):
            raise TypeError('Код валюты должен быть представлен строкой.')
        self.currency_code = currency_code.upper()
        self._balance = balance
    
    def deposit(self, amount: float):
        """ Метод для пополнения баланса """
        if not isinstance(amount, float):
            raise TypeError('Сумма пополнения баланса должна быть числом.')
        if amount <= 0:
            raise ValueError('Сумма пополнения баланса должна быть больше 0.')
        self._balance += amount 
        return self._balance
    
    def withdraw(self, amount: float):
        """ Метод для снятия средств, если позволяет баланс """
        if not isinstance(amount, float):
            raise TypeError('Сумма снятия средств должна быть числом.')
        if amount <= 0:
            raise ValueError('Сумма списания должна быть больше 0.')
        if amount > self._balance:
            raise ValueError('На балансе недостаточно средств.')
        self._balance -= amount
        return self._balance

    def get_balance_info(self):
        """ Вывод информации о текущем балансе """
        return {
            'currency_code': self.currency_code,
            'balance': self._balance
        }
    
    @property 
    def balance(self):
        return self._balance
    
    @balance.setter 
    def balance(self, amount: float):
        if not isinstance(amount, float):
            raise TypeError('Баланс должен быть числом.')
        if amount < 0:
            raise ValueError('Баланс не может быть отрицательным.')
        self._balance = amount 
    

class Portfolio:
    """
    Класс управления всеми кошельками одного пользователя
    """
    def __init__(
            self, 
            user_id: int, 
            wallets: dict[str, Wallet]
        ):
        """
        Конструктор класса Portfolio

        user_id: уникальный идентификатор пользователя
        wallets: словарь кошельков, где ключ - код валюты, значение - объект кошелька
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError('Идентификатор пользователя должен быть целым числом.')
        self._user_id = user_id

        if not isinstance(wallets, dict):
            raise TypeError('Кошельки пользователя должны передаваться в словаре.')
        if not all(isinstance(code, str) for code in wallets):
            raise TypeError('Коды валют в словаре кошельков должны быть строками.')
        if not all(isinstance(wallet, Wallet) for wallet in wallets.values()):
            raise TypeError('Значения в словаре кошельков должны быть объектами Wallet кошелька.')
        self._wallets = wallets 
    
    @property 
    def user(self):
        return self._user_id
    
    @property
    def wallet(self):
        return self._wallet.copy()
    
    def add_currency(self, currency_code: str):
        """
        Добавляет новый кошелек в портфель, если его еще нет.
        """
        if not isinstance(currency_code, str):
            raise TypeError('Код валюты должен быть представлен строкой.')
        if currency_code in self._wallets:
            raise ValueError(f'Кошелек с валютой {currency_code} уже есть в портфеле.')
        currency_code = currency_code.upper()
        new_wallet = Wallet(currency_code)
        self._wallets[currency_code] = new_wallet
    
    def get_wallet(self, currency_code: str):
        """ 
        Возвращает существующий объект класса Wallet по коду валюты.
        """
        if not isinstance(currency_code, str):
            raise TypeError('Код валюты должен быть строкой')
        if currency_code in self._wallets:
            return self._wallets.get(currency_code)
        else:
            raise ValueError(f'Кошелька с валютой {currency_code} нет в портфеле.')
    
    def _get_rates(self, base_currency: str):
        """
        Запрашивает и возвращает курсы валют для заданной валюты.
        """
        if not isinstance(base_currency, str):
            raise TypeError('Код валюты должен быть строкой.')
        base_currency = base_currency.upper()
        url = f'{BASE_URL_EXCHANGE_RATE}{API_KEY}/latest/{base_currency}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        result = data.get('result')

        if result == 'success':
            rates = data.get('conversion_rates')
            if rates:
                return rates 
            else:
                raise ValueError(('API вернул успешный ответ, '
                    f'но не содержит блока "курсы обмена" для {base_currency}'))
        elif result == 'error-code':
            error_type = data.get('error_type')
            raise ValueError(f'Ошибка API: {error_type}')
        else: 
            raise ValueError(f'Неожиданный формат ответа API для {base_currency}: {data}')

    def get_total_value(self, base_currency='USD'):
        """
        Возвращает общую стоимость всех валют пользователя в указанной базовой валюте.
        По умолчанию базовая валюта - 'USD'.
        """
        if not isinstance(base_currency, str):
            raise TypeError('Код валюты должен быть строкой.')
        base_currency = base_currency.upper()
        total_balance = []
        for currency, wallet in self._wallets.items():
            if currency == base_currency:
                balance = wallet.get('balance')
                if balance:
                    total_balance.append(balance)
            else:
                rates = self._get_rates(base_currency)
                if currency not in rates:
                    raise ValueError((f'Курс для валюты {currency} '
                    f'относительно {base_currency} не найден в API.'))
                currency_rate = rates.get(currency)
                currency_balance = wallet.get('balance')
                balance = currency_balance / currency_rate
                total_balance.append(balance)
        return sum(total_balance)