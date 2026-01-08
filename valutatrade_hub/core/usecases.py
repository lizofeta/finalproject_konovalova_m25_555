# Модуль содержит бизнес-логику приложения
from datetime import datetime, timedelta, timezone

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    RateUnavailableError,
    ShortPasswordError,
    UsernameAlreadyTakenError,
    UserNotFoundError,
    UserUnlogedError,
    WrongPasswordError,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager, get_database
from valutatrade_hub.infra.settings import SettingsLoader, get_settings
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater


class Session:
    """
    Класс управления сессией пользователя.
    """
    def __init__(self):
        self.current_user = None 
    
    def is_logged_in(self):
        """ Проверить, залогинен ли пользователь """
        return self.current_user is not None 
    
    def login(self, user:User):
        """ Залогинить пользователя """
        self.current_user = user 
    
    def logout(self):
        """ Разлогинить пользователя """
        self.current_user = None 
    
    def get_current_user(self):
        """ Получить текущего пользователя """
        return self.current_user 
    

class UserCommands:
    """ 
    Класс для работы с пользователями

    Команды:
        register - регистрация
        login - вход 
    """
    def __init__(
            self, 
            session:Session, 
            settings:SettingsLoader = None, 
            database:DatabaseManager = None
        ):
        self.session = session
        if settings:
            self.settings = settings
        else:
            self.settings = get_settings()
        
        if database:
            self.database = database 
        else:
            self.database = get_database()
    
    @log_action(action='REGISTER', verbose=False)
    def register(self, username:str, password:str, initial_usd_amount:float|int):
        """
        Регистрация нового пользователя.

        Аргументы:
            username:str - имя нового пользователя
            password:str - пароль нового пользователя
            initial_usd_amount - начальная сумма пополнения баланса USD-кошелька
        
        Возвращает:
            Сообщение об успешной регистрации.

        Выбрасывает:
            ValueError,
            TypeError,
            ShortPasswordError,
            UsernameAlreadyTakenError
        """
        if not username or not username.strip():
            raise ValueError('Имя пользователя не должно быть пустым.')
        if not isinstance(initial_usd_amount, float|int):
            raise TypeError\
            ("Начальная сумма пополнения USD кошелька должна быть числом.")
        if initial_usd_amount <= 0:
            raise ValueError(("Начальная сумма пополнения USD "
                             "кошелька должна быть положительным числом."))

        # Проверка длины пароля
        if len(password) < 4:
            raise ShortPasswordError('Пароль должен быть не короче 4-х символов.')

        # Проверка уникальности имени пользователя
        if self.database.find_user_by_username(username):
            raise UsernameAlreadyTakenError(username)
        
        # Генерация нового id
        users = self.database.load_users()
        new_id = max([user.user_id for user in users], default=0) + 1

        # Создание нового объекта пользователя
        new_user = User(new_id, username, password)
        users.append(new_user)
        self.database.save_users(users)

        # Создание нового портфолио с созданием и пополнением USD-кошелька
        portfolios = self.database.load_portfolios()
        new_portfolio = Portfolio(new_id)
        new_portfolio.add_currency('USD', initial_usd_amount)
        portfolios.append(new_portfolio)
        self.database.save_portfolios(portfolios)

        return (f"Пользователь с именем {username} "
            f"успешно зарегистрирован под id={new_id}."
            f"\nСоздан USD-кошелек с начальным балансом: {initial_usd_amount}")

    @log_action(action='LOGIN', verbose=False)
    def login(self, username:str, password:str):
        """
        Войти и зафиксировать текущую сессию.

        Аргументы:
            username - имя пользователя
            password - пароль
        
        Возвращает:
            Сообщение о входе
        
        Выбрасывает:
            ValueError,
            UserNotFoundError,
            WrongPasswordError
        """
        if not username or not username.strip():
            raise ValueError("Имя пользователя не должно быть пустым.")
        if not self.database.find_user_by_username(username):
            raise UserNotFoundError(username)
        
        user = self.database.find_user_by_username(username)
        if user.verify_password(password) is False:
            raise WrongPasswordError()
        
        self.session.login(user)
        return f"Вы успешно вошли под именем '{username}'."
    

class PortfolioCommands:
    """
    Класс для работы с портфелями пользователей
    """
    def __init__(
            self,
            session:Session,
            database:DatabaseManager = None,
            settings:SettingsLoader = None
        ):
        self.session = session 

        if settings:
            self.settings = settings
        else:
            self.settings = get_settings()
        
        if database:
            self.database = database 
        else:
            self.database = get_database()
    
    def show_portfolio(self, base:str = 'USD'):
        """
        Показать все кошельки и итоговую стоимость в базовой валюте (по умолчанию USD).

        Аргументы:
            base:str (необязательный) - базовая валюта
        
        Возвращает:
            Отформатированную информацию о портфеле пользователя
        
        Выбрасывает:
            UserUnlogedError
        """
        if not self.session.is_logged_in():
            raise UserUnlogedError()
        if base != 'USD':
            base = base.upper()
            # Валидация существования валюты:
            get_currency(base)
            
        user = self.session.get_current_user()
        user_id = user.user_id
        portfolio = self.database.find_portfolio_by_user_id(user_id)

        if not portfolio._wallets:
            return (f"Портфель пользователя {user.username} пуст. "
                    "Используйте команду 'buy' для покупки валюты.")
        result = [f"Портфель пользователя {user.username} (база: {base}):"]

        total_balance = 0.0
        for code, wallet in portfolio._wallets.items():
            balance = wallet.balance 
            # в базовой валюте:
            if code == base:
                balance_base = wallet.balance 
            else:
                rate = self.database.get_rate(code, base)
                if rate:
                    balance_base = wallet.balance * rate 
                else:
                    result.append(f" {code}: {balance:.2f} -> курс недоступен")
                    continue 
            total_balance += balance_base
            result.append(f"- {code}: {balance:.2f} -> {base}: {balance_base:.2f}")
        
        result.append("---------------------------------")
        result.append(f"ИТОГО: {total_balance:.2f} {base}")

        return "\n".join(result)
    
    @log_action(action='BUY', verbose=True)
    def buy(self, currency:str, amount:float|int):
        """
        Метод для покупки валют. Покупка других валют возможна только за USD.

        Аргументы:
            currency:str - код покупаемой валюты (например, BTC).
            amount:float - количество покупаемой валюты.
        
        Возвращает: 
            Сообщение об успешной покупке.
        
        Выбрасывает:
            UserUnlogedError,
            TypeError,
            ValueError,
            RateUnavailableError,
            InsufficientFundsError
        """
        # Проверка login
        if not self.session.is_logged_in():
            raise UserUnlogedError()
        
        # Валидация кода покупаемой валюты
        if not isinstance(currency, str):
            raise TypeError("Код валюты должен быть строкой.")
        get_currency(currency.strip())

        # Валидация количества покупаемой валюты (amount > 0)
        if not isinstance(amount, float|int):
            raise TypeError("Количество покупаемой валюты должно быть числом.")
        if amount <= 0:
            raise ValueError\
            ("Количество покупаемой валюты должно быть положительным числом.")
        
        # Проверка наличия кошелька и его создание в случае отсутствия
        user = self.session.get_current_user()
        user_id = user.user_id 
        portfolio = self.database.find_portfolio_by_user_id(user_id)
        try:
            wallet = portfolio.get_wallet(currency)
        except ValueError:
            # Создание нового кошелька
            wallet = portfolio.add_currency(currency)
        
        # Получаем курс currency_USD:
        rate = self.database.get_rate(currency, 'USD')
        if rate:
            usd_price = rate * amount 
        else:
            raise RateUnavailableError(currency, 'USD')
        
        usd_old_balance = portfolio.get_wallet('USD').balance
        currency_old_balance = wallet.balance

        # Снимаем стоимость валюты в долларах с USD-кошелька.
        portfolio.get_wallet('USD').withdraw(usd_price)
        usd_new_balance = portfolio.get_wallet('USD').balance

        # Кладем на счет покупаемой валюты купленную сумму
        portfolio.get_wallet(currency).balance += amount
        currency_new_balance = portfolio.get_wallet(currency).balance

        # Сохраняем портфель с изменениями
        self.database.save_portfolio(portfolio)

        result = (
            f"Покупка выполнена: {amount} {currency} "
            f"по курсу {rate} USD/{currency}"
            f"\nИзменения в портфеле:"
            f"\n{currency}: было {currency_old_balance:.4f} "
            f"-> стало {currency_new_balance:.4f}"
            f"\nUSD: было {usd_old_balance:.2f} -> стало {usd_new_balance:.2f}"
            f"\nОценочная стоимость покупки: {usd_price:.2f} USD"
        )

        return result 
    
    @log_action(action='BUY_USD', verbose=True)
    def buy_usd(self, amount:float):
        """
        Метод для покупки USD за деньги из внешнего источника (имитация)

        Аргументы:
            amount:float - количество покупаемых USD
        """
        # Проверка на выполненный вход в систему
        if not self.session.is_logged_in():
            raise UserUnlogedError()
        
        # Валидация количества покупаемой валюты (amount > 0)
        if not isinstance(amount, float|int):
            raise TypeError("Количество покупаемой валюты должно быть числом.")
        if amount <= 0:
            raise ValueError\
            ("Количество покупаемой валюты должно быть положительным числом.")
        
        # Перевод на USD счет указанное количество долларов:
        user_id = self.session.get_current_user().user_id 
        portfolio = self.database.find_portfolio_by_user_id(user_id)
        usd_old_balance = portfolio.get_wallet('USD').balance 
        portfolio.get_wallet('USD').deposit(amount)
        usd_new_balance = portfolio.get_wallet('USD').balance 
        self.database.save_portfolio(portfolio)

        return (f"Покупка выполнена: {amount} USD"
                "\nИзменения в портфеле: "
                f"USD: было {usd_old_balance:.2f} -> стало {usd_new_balance:.2f}")
    
    @log_action(action='SELL', verbose=True)
    def sell(self, currency:str, amount:float|int):
        """
        Метод для продажи валют. Возможна продажа всех валют, 
        поддерживаемых приложением, кроме USD.
        Стоимость валюты рассчитывается по актуальному курсу и 
        после продажи начисляется в USD валюте на соответствующий счет.

        Аргументы: 
            currency:str - код продаваемой валюты
            amount:float|int - количество продаваемой валюты
        
        Возвращает:
            Сообщение об успешной продаже
        
        Выбрасывает:
            TypeError,
            ValueError,
            UserUnlogedError,
            RateUnavailableError,
            InsufficientFundsError
        """
        # Проверка на выполненный вход в систему
        if not self.session.is_logged_in():
            raise UserUnlogedError()

        # Валидация кода покупаемой валюты
        if not isinstance(currency, str):
            raise TypeError("Код валюты должен быть строкой.")
        if currency == 'USD':
            raise ValueError('Продажа USD не допускается.')
        get_currency(currency.strip())

        # Валидация количества покупаемой валюты (amount > 0)
        if not isinstance(amount, float|int):
            raise TypeError("Количество покупаемой валюты должно быть числом.")
        if amount <= 0:
            raise ValueError\
            ("Количество покупаемой валюты должно быть положительным числом.")
        
        # Проверка существования кошелька 
        # (при отсутствии - ValueError в методе get_wallet())
        user_id = self.session.get_current_user().user_id 
        portfolio = self.database.find_portfolio_by_user_id(user_id)
        try:
            wallet = portfolio.get_wallet(currency)
        except ValueError as e:
            raise ValueError(
                f'{e}. Добавьте валюту: она создается автоматически при первой покупке.'
            ) from e

        # Получение курса продаваемой валюты к доллару
        rate = self.database.get_rate(currency, 'USD')
        if not rate:
            raise RateUnavailableError(currency, 'USD')
        
        currency_old_balance = wallet.balance 
        usd_old_balance = portfolio.get_wallet('USD').balance 

        # Списание средств со счета продаваемой валюты
        # InsufficientFundsError, если недостаточно средств:
        portfolio.get_wallet(currency).withdraw(amount) 
        currency_new_balance = portfolio.get_wallet(currency).balance

        # Кладем на счет USD цену за продаваемую валюту
        portfolio.get_wallet('USD').deposit(rate * amount)
        usd_new_balance = portfolio.get_wallet('USD').balance 

        # Сохраняем измененный портфель
        self.database.save_portfolio(portfolio)

        result = (
            f"Покупка выполнена: {amount} {currency} "
            f"по курсу {rate} USD/{currency} "
            "\nИзменения в портфеле:"
            f"\n{currency}: было {currency_old_balance:.4f} "
            f"-> стало {currency_new_balance:.4f}"
            f"\nUSD: было {usd_old_balance:.2f} -> стало {usd_new_balance:.2f}"
            f"\nОценочная выручка: {rate * amount:.2f} USD"
        )

        return result 
    

class RatesCommands:
    def __init__(self):
        self.database = DatabaseManager()
        self.settings = SettingsLoader()
        self.config = ParserConfig()
        self.updater = RatesUpdater(self.config)

    def get_rate(self, currency_from:str, currency_to:str):
        """
        Получить текущий курс одной валюты к другой.

        Аргументы:
            currency_from:str - код исходной валюты
            currency_to:str - код целевой валюты

        Возвращает:
            Сообщение с прямым и обратным курсами.

        Выбрасывает:
            TypeError,
            ValueError,
            CurrencyNotFoundError
        """
        # Проверка валидности курсов валют
        if not isinstance(currency_from, str) or not isinstance(currency_to, str):
            raise TypeError('Коды валют должны быть строками.')
        if not currency_from.strip() or not currency_to.strip():
            raise ValueError('Коды валют не должны быть пустыми.')
        currency_from = currency_from.upper()
        currency_to = currency_to.upper()

        # Валидация существования валюты
        get_currency(currency_from)
        get_currency(currency_to)

        # Попытка взять курс из локального кэша (rates.json)
        # Если курс свежий (моложе 5 минут), берем его, 
        # иначе - запрашиваем у внешнего источника через Parser Service
        rates_data = self.database.load_rates()
        ttl = self.settings.get_rates_ttl() # ttl = 300 секунд
        if not rates_data:
            raise RateUnavailableError(
                'Локальный кэш пуст. '
                'Выполните update-rates, чтобы загрузить данные'
            )
        updated_at = rates_data.get('last_refresh')
        # Извлекаем курсы
        pair_rate = self.database.get_rate(currency_from, currency_to)
        reversed_pair_rate = 1 / pair_rate
        # Проверяем, просрочены ли данные
        updated_at_dt = datetime.fromisoformat(updated_at).replace(microsecond=0)
        updated_display = updated_at.replace('Z', '').replace('T', ' ')
        if datetime.now(timezone.utc) < updated_at_dt + timedelta(seconds=int(ttl)):
            return (f"Курс {currency_from}->{currency_to}: {pair_rate:.6f} "
                    f"(обновлено: {updated_display})"
                    f"\nОбратный курс: {currency_to}->{currency_from}:"
                    f" {reversed_pair_rate:.6f}")
        else:
            # данные просрочены: обновляем через RatesUpdater
            self.updater.run_update()
            # Извлекаем новые курсы
            new_rates_data = self.database.load_rates()
            if not new_rates_data:
                raise RateUnavailableError(
                    'Локальный кэш пуст. '
                    'Выполните update-rates, чтобы загрузить данные'
                )
            new_updated_at = new_rates_data.get('last_refresh')
            new_rate = self.database.get_rate(currency_from, currency_to)
            if new_updated_at:
                new_updated_at_display = new_updated_at\
                    .replace('T', ' ').replace('Z', '')
            new_reversed_rate = 1/new_rate if new_rate > 0 else 0
            return (
                f"Курс {currency_from}->{currency_to}: {new_rate:.6f} "
                f"(обновлено: {new_updated_at_display}) "
                f"\nОбратный курс {currency_to}->{currency_from}: "
                f"{new_reversed_rate:.6f}"
            )
    
    def show_rates(
            self, 
            currency:str=None, 
            top:int=None,
            base:str='USD'
        ):
        # Проверки
        if not currency and not top:
            raise ValueError("Необходимо указать хотя бы "
                             "один аргумент: либо currency, либо top")
        if currency and top:
            raise ValueError('Нельзя комбинировать аргументы currency & top.')
        # Валидация числа топа
        if top:
            if top <= 0:
                raise ValueError\
                    ('Количество криптовалют должно быть положительным')
        # Загружаем курсы из кэша
        rates_data = self.database.load_rates()
        if rates_data:
            rates = rates_data.get('rates')
            last_updated_at = rates_data.get('last_refresh', 'информация отсутствует')
        else:
            raise RateUnavailableError(extra_info=". Локальный кэш пуст. "
                    "Выполните update-rates, чтобы загрузить данные.")
        if last_updated_at != 'информация отсутствует':
                updated_at_display = last_updated_at\
                    .replace('T', ' ').replace('Z', '')
        else:
            updated_at_display = last_updated_at
        # Обрабатываем сценарий получения курса конкретной валюты
        if currency:
            # Валидируем коды валют
            get_currency(currency)
            get_currency(base)
            # Формируем пару 
            pair = f"{currency.upper()}_{base.upper()}"
            # Пробуем получить курс для сформированной пары валют
            pair_rate = rates.get(pair)
            if not pair_rate:
                raise RateUnavailableError(
                    currency_from=currency,
                    currency_to=base,
                    extra_info=(f"Курс для пары {pair} "
                    "не найден в кэше. Выполните update-rates, "
                    f"указав базой {base} и повторите попытку.")
                )
            rate = pair_rate.get('rate')
            if not rate:
                raise RateUnavailableError(
                    currency_from=currency,
                    currency_to=base
                )
            return (f"Курс для {currency} относительно {base} "
                    f"из кэша (обновлено: {updated_at_display})"
                    f"\n- {pair}: {rate:.5f}")
        # ОБрабатываем сценарий с получением курсов для топ N криптовалют 
        if top is not None:
            crypto_coins = list(self.config.CRYPTO_ID_MAP.keys())
            crypto_rates = []
            for code in crypto_coins:
                # Формируем пару
                pair = f"{code}_{base}"
                # Пробуем извлечь курс для пары
                pair_rate = rates.get(pair)
                if not pair_rate:
                    raise RateUnavailableError(
                        currency_from=code,
                        currency_to=base,
                        extra_info=(f"Курс для пары {pair} "
                        "не найден в кэше. Выполните update-rates, "
                        f"указав базой {base} и повторите попытку.")
                    )
                # Извлекаем и сохраняем курс
                rate = pair_rate.get('rate')
                if not rate:
                    raise RateUnavailableError(
                    currency_from=code,
                    currency_to=base
                    )
                crypto_rates.append((code, rate))
            if top > len(crypto_rates):
                raise RateUnavailableError(
                    extra_info=(f' Всего извлечено {len(crypto_rates)}.'
                                f' Запрошено: {top}.')
                    )
            # Получаем топ N сортировкой и срезом 
            top_n = sorted(
                crypto_rates, 
                key=lambda x: x[1], 
                reverse=True
            )[:top]

            # Формируем итоговую отформатированную строку
            result = f"Курсы из локального кэша (обновлено: {updated_at_display})"
            for code, rate in top_n:
                result += f"\n- {code}_{base}: {rate:.2f}"
            
            return result