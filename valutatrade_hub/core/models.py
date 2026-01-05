""" Модуль содержит основные модели данных проекта """

import datetime
import hashlib
import uuid

from valutatrade_hub.core.exceptions import InsufficientFundsError


class User:
    """ Класс пользователя """

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """
        Генерирует односторонний псевдо-хеш пароля, используя соль
        """
        if not isinstance(password, str) or not isinstance(salt, str):
            raise TypeError('Пароль и соль должны быть строками.')
        salted_password = (password + salt).encode('utf-8')
        return hashlib.sha256(salted_password).hexdigest()


    def __init__(
            self, 
            user_id: int, 
            username: str, 
            password: str,
            hashed_password: str = None, 
            salt: str = None, 
            registration_date: datetime = None
        ): 
        """
        Конструктор класса User

        user_id: уникальный идентификатор пользователя
        username: имя пользователя
        password: пароль в открытом виде (если пользователь еще не зарегистрирован)
        hashed_password: пароль в зашифрованном виде
        salt: уникальная соль для пользователя
        registration_date: дата регистрации пользователя
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError\
            ('Уникальный идентификатор должен быть целым положительным числом.')
        self._user_id = user_id
        self._username = username 

        if password and not hashed_password:
            self._salt = uuid.uuid4.hex()
            self._hashed_password = self._hash_password(password, self._salt)
        elif hashed_password and salt:
            if not isinstance(hashed_password, str) or not isinstance(salt, str):
                raise TypeError\
                ('Хешированный пароль и соль должны быть представлены строками.')
            self._salt = salt 
            self._hashed_password = hashed_password
        else:
            raise ValueError\
            ('Необходимо указать либо открытый пароль (при регистрации),\
 либо захешированный + соль (для зарегистрированного пользователя).')

        if registration_date:
            if not isinstance(registration_date, datetime.datetime):
                raise TypeError('Дата регистрации должна быть объектом datetime')
            self._registration_date = registration_date 
        else:
            self._registration_date = datetime.datetime.now()

    # Геттеры
    @property
    def user_id(self):
        return self._user_id
    
    @property
    def username(self):
        return self._username 
    
    @property
    def hashed_password(self):
        return self._hashed_password
    
    @property
    def salt(self):
        return self._salt 
    
    @property
    def registration_date(self):
        return self._registration_date
    
    # Сеттеры
    @username.setter
    def username(self, value: str):
        if not isinstance(value, str):
            raise TypeError('Имя должно быть представленно строкой.')
        if not value.strip():
            raise ValueError('Имя не должно быть пустым.')
        self._username = value.strip()
    
    def get_user_info(self):
        """Возвращает информацию о пользователе (без пароля)"""
        return {
            'user_id': self._user_id,
            'username': self._username,
            'registration_date': self._registration_date.isoformat()
        }
    
    def change_password(self, new_password: str):
        """
        Изменяет пароль пользователя, хешируя новый пароль с новой солью.
        """
        if len(new_password.strip()) < 4:
            raise ValueError('Пароль должен быть не короче 4 символов.')
        new_salt = uuid.uuid4().hex
        self._salt = new_salt 
        self._hashed_password = self._hash_password(new_password, new_salt)

    def verify_password(self, password):
        """
        Проверяет введенный пользователем пароль на совпадение с сохраненным 
        хешированнвм паролем.
        """
        if not isinstance(password, str):
            return False
        password_to_verify = self._hash_password(password, self._salt)
        return password_to_verify == self._hashed_password
    
    def to_dict(self):
        """ Конвертирует пользователя в словарь для сохранения в файл JSON """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """ 
        Создает экземпляр пользователя из словаря, пришедшего из внешнего источника.
        """
        return cls(
            user_id = data.get('user_id'),
            username = data.get('username'),
            hashed_password = data.get('hashed_password'),
            salt = data.get('salt'),
            registration_date = datetime.fromisoformat(data.get('registration_date'))
        )


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
        if not isinstance(amount, (int, float)):
            raise TypeError('Сумма пополнения баланса должна быть числом.')
        if amount <= 0:
            raise ValueError('Сумма пополнения баланса должна быть больше 0.')
        self._balance += float(amount) 
    
    def withdraw(self, amount: float):
        """ Метод для снятия средств, если позволяет баланс """
        if not isinstance(amount, (int, float)):
            raise TypeError('Сумма снятия средств должна быть числом.')
        if amount <= 0:
            raise ValueError('Сумма списания должна быть больше 0.')
        if amount > self._balance:
            raise InsufficientFundsError(
                available=self._balance, 
                code=self.currency_code,
                required=amount
            )
        self._balance -= float(amount)
        return self._balance

    def get_balance_info(self):
        """ Вывод информации о текущем балансе """
        return {
            'currency_code': self.currency_code,
            'balance': self._balance
        }
    
    # Геттеры
    @property 
    def balance(self):
        return self._balance
    
    @balance.setter 
    def balance(self, amount: float):
        if not isinstance(amount, (int, float)):
            raise TypeError('Баланс должен быть числом.')
        if amount < 0:
            raise ValueError('Баланс не может быть отрицательным.')
        self._balance = float(amount) 

    def to_dict(self):
        """ Конвертирует кошелек в словарь """
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }
    
    @classmethod 
    def from_dict(cls, data: dict):
        """ Создает экземпляр кошелька из словаря """
        return cls(
            currency_code = data.get('currency_code'),
            balance = data.get('balance')
        )
    

class Portfolio:
    """
    Класс управления всеми кошельками одного пользователя
    """
    def __init__(
            self, 
            user_id: int, 
            wallets: dict[str, Wallet] = {}
        ):
        """
        Конструктор класса Portfolio

        user_id: уникальный идентификатор пользователя
        wallets: словарь кошельков, где ключ - код валюты, значение - объект кошелька
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError('Идентификатор пользователя должен быть целым числом.')
        self._user_id = user_id
        
        if wallets:
            if not isinstance(wallets, dict):
                raise TypeError('Кошельки пользователя должны передаваться в словаре.')
            if not all(isinstance(code, str) for code in wallets):
                raise TypeError('Коды валют в словаре кошельков должны быть строками.')
            if not all(isinstance(wallet, Wallet) for wallet in wallets.values()):
                raise TypeError\
                ('Значения в словаре кошельков должны быть объектами Wallet кошелька.')
            self._wallets = wallets 
        else:
            self._wallets = {}
    
    # Геттеры
    @property 
    def user(self):
        return self._user_id
    
    @property
    def wallet(self):
        return self._wallets.copy()
    
    def add_currency(self, currency_code: str, initial_balance: float = 0.0):
        """
        Добавляет новый кошелек в портфель, если его еще нет.
        """
        if not isinstance(currency_code, str):
            raise TypeError('Код валюты должен быть представлен строкой.')
        if currency_code in self._wallets:
            raise ValueError(f'Кошелек с валютой {currency_code} уже есть в портфеле.')
        currency_code = currency_code.upper()
        new_wallet = Wallet(currency_code, initial_balance)
        self._wallets[currency_code] = new_wallet
    
    def get_wallet(self, currency_code: str):
        """ 
        Возвращает существующий объект класса Wallet по коду валюты.
        """
        if not isinstance(currency_code, str):
            raise TypeError('Код валюты должен быть строкой')
        currency_code = currency_code.upper()
        if currency_code in self._wallets:
            return self._wallets.get(currency_code)
        else:
            raise ValueError(f'Кошелька с валютой {currency_code} нет в портфеле.')

    def get_total_value(
            self, 
            base_currency='USD', 
            exchange_rates: dict[str, float] = None):
        """
        Возвращает общую стоимость всех валют пользователя в указанной базовой валюте.
        По умолчанию базовая валюта - 'USD'.
        """
        if not isinstance(base_currency, str):
            raise TypeError('Код валюты должен быть строкой.')
        base_currency = base_currency.upper()
        total_balance = 0
        for currency, wallet in self._wallets.items():
            if currency == base_currency:
                balance = wallet.get('balance')
                if balance:
                    total_balance += balance
            else:
                if exchange_rates is None:
                    exchange_rates = {
                        "EUR_USD": 1.1587,
                        "BTC_USD": 59337.21,
                        "RUB_USD": 0.01237,
                        "ETH_USD": 3720.00,
                        "USD_USD": 1.0
                    }
                rate_key = f'{currency}_{base_currency}'
                if rate_key not in exchange_rates:
                    raise ValueError((f'Курс для валюты {currency} '
                    f'относительно {base_currency} не найден.'))
                currency_rate = exchange_rates.get(rate_key)
                currency_balance = wallet.get('balance')
                balance = currency_balance / currency_rate
                total_balance += balance
        return total_balance
    
    def to_dict(self):
        """ Конвертирует портфель в словарь """
        return {
            "user_id": self._user_id,
            "wallets": {
                code: wallet.to_dict() for code, wallet in self._wallets.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """ Создает экземпляр портфеля из словаря """
        wallets = {
            code: Wallet.from_dict(wallet)
            for code, wallet in data.get('wallets', {}).items()
        }
        return cls(
            user_id = data.get('user_id'),
            wallets = wallets
        )