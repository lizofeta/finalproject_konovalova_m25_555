from valutatrade_hub.core.utils import (
    load_data, 
    save_data,
    validate_currency_code
    )
from valutatrade_hub.core.constants import (
    BASE_URL_EXCHANGE_RATE,
    API_KEY,
    USER_DATA_PATH, 
    PORTFOLIOS_DATA_PATH, 
    RATES_DATA_PATH
    )
from valutatrade_hub.core.utils import hash_password
from valutatrade_hub.decorators import handle_errors
import uuid 
from  datetime import datetime, timedelta, timezone
import requests
import json

@handle_errors
def get_rate(from_currency: str, to_currency: str) -> dict:
    """
    Функция получения текущего курса одной валюты к другой.
    """
    if not validate_currency_code(from_currency):
        return 
    if not validate_currency_code(to_currency):
        return

    # загружаем данные из кеша
    rates_cache = load_data(RATES_DATA_PATH)
    if rates_cache:
        if from_currency in rates_cache and to_currency in rates_cache.get(from_currency):
            rate = rates_cache[from_currency][to_currency]['rate']
            reversed_rate = rates_cache[to_currency][from_currency]['rate']
            updated_at = rates_cache[from_currency][to_currency]['updated_at']
            updated_at_reversed = rates_cache[to_currency][from_currency]['updated_at']
            updated_object = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%S")
            updated_object_reversed = datetime.strptime(updated_at_reversed, "%Y-%m-%dT%H:%M:%S")
            current_time = datetime.now() 
            # проверяем данные на актуальность
            threshold = timedelta(days=2) 
            if (current_time - updated_object) < threshold and \
            (current_time - updated_object_reversed) < threshold:
                return {
                    "rate": rate,
                    "reversed_rate": reversed_rate,
                    "updated_at": updated_at
                    }
    # Если данные в кеше устарели, запрашиваем новые
    url_rate = f"{BASE_URL_EXCHANGE_RATE}{API_KEY}/latest/{from_currency}"
    response = requests.get(url_rate)
    response.raise_for_status()
    data = response.json()
    status = data.get('result')
    if status == 'success':
        rate_api = data['conversion_rates'][to_currency]
        reversed_rate_api = round(1 / rate_api, 5)
        last_update_unix = data['time_last_update_unix']
        last_update_datetime = datetime.fromtimestamp(last_update_unix, tz=timezone.utc)
        last_update_str = datetime.strftime(last_update_datetime, "%Y-%m-%dT%H:%M:%S")
        # Обновляем данные в кеше
        rates_cache[from_currency][to_currency]['rate'] = rate_api 
        rates_cache[to_currency][from_currency]['rate'] = reversed_rate_api 
        rates_cache[from_currency][to_currency]['updated_at'] = last_update_str
        rates_cache[to_currency][from_currency]['updated_at'] = last_update_str
        # Сохраняем данные в кеше
        save_data(RATES_DATA_PATH, rates_cache)
        return {
            "rate": rate_api,
            "reversed_rate": reversed_rate_api,
            "updated_at": last_update_str
        }
    elif status == 'error_code':
        error_type = data.get('error_type')
        raise ValueError(f'Ошибка API: {error_type}')
    else:
        raise ValueError(f'Неожиданный формат ответа API для {from_currency}: {data}')


@handle_errors
def register(username: str, password: str, initial_amount: float | int):
    """
    Функция регистрации пользователя.
    """
    if not isinstance(username, str):
        raise ValueError('Имя пользователя должно быть строкой.')
    if not username.strip():
        raise ValueError('Имя пользователя не должно быть пустым.')
    if not isinstance(password, str):
        raise TypeError('Пароль должен иметь строковый вид.')
    if len(password) < 4:
        raise ValueError('Пароль должен быть не короче 4-х символов.')
    if not isinstance(initial_amount, (float, int)):
        raise TypeError('Сумма пополнения баланса должна иметь тип float.')
    if initial_amount <= 0:
        raise ValueError('Сумма пополнения баланса должна быть положительной.')

    users_data = load_data(USER_DATA_PATH)
    portfolios_data = load_data(PORTFOLIOS_DATA_PATH)

    if not users_data:
        user_id = 1
    else:
        taken_user_names = [user.get('username') for user in users_data]
        if username in taken_user_names:
            raise ValueError(f'Имя пользователя {username} уже занято.')
        max_user_id = max([user.get('user_id') for user in users_data])
        user_id = max_user_id + 1

    salt = uuid.uuid4().hex
    hashed_password = hash_password(password, salt)

    user = {
        'user_id': user_id,
        'username': username,
        'salt': salt,
        'hashed_password': hashed_password,
        'registration_date': datetime.now().isoformat()
    }
    users_data.append(user)
    save_data(USER_DATA_PATH, users_data)

    portfolio = {
        'user_id': user_id,
        'wallets': {
            'USD': {'balance': initial_amount}
        }
    }
    portfolios_data.append(portfolio)
    save_data(PORTFOLIOS_DATA_PATH, portfolios_data)

    return f'Пользователь {username} успешно зарегестрирован (id={user_id}). Войдите в систему.'


@handle_errors
def login(username: str, password: str):
    """
    Функция для входа и фиксации текущей сессии.
    """
    if not isinstance(username, str):
        raise TypeError('Имя пользователя должно быть строкой.')
    if not isinstance(password, str):
        raise TypeError('Пароль должен иметь строковый тип.')
    if not username.strip() or not password.strip():
        raise ValueError(('Имя пользователя и пароль '
        'обязательны для заполнения и не должны быть пустыми.'))
    
    users_data = load_data(USER_DATA_PATH)
    if not users_data:
        raise ValueError('В системе еще нет зарегестрированных пользователей.')
    usernames = [user['username'] for user in users_data]
    if username not in usernames:
        raise ValueError(f'Пользователь {username} не зарегестрирован.')
    for user in users_data:
        if user['username'] == username:
            user_id = user['user_id']
            salt = user['salt']
            true_password = user['hashed_password']
            input_password = hash_password(password, salt)
            return {"login_state": true_password == input_password,
                    "user_id": user_id}

@handle_errors
def show_portfolio(user_id: int, base='USD'):
    """
    Выводит информацию о кошельках пользователя и итоговую стоимость в базовой валюте.
    Базовая валюта по умолчанию: 'USD'.
    """
    if not isinstance(user_id, int):
        raise TypeError('Идентификатор пользователя должен быть числом.')
    validate_currency_code(base)
    portfolios = load_data(PORTFOLIOS_DATA_PATH)
    user_portfolio = None
    for portfolio in portfolios:
        if isinstance(portfolio, dict) and portfolio.get('user_id') == user_id:
            user_portfolio = portfolio
            break 
    if not user_portfolio:
        raise ValueError(f'Портфолио пользователя c id={user_id} не был найден.')
    user_wallets = user_portfolio.get('wallets')
    if not user_wallets or not isinstance(user_wallets, dict):
        print(f'У пользователя c id={user_id} нет кошельков или они имеют неверный формат.')
        return
    else:
        rates = load_data(RATES_DATA_PATH)
        base_currency_rates = rates.get(base)
        if not base_currency_rates or not isinstance(base_currency_rates, dict):
            print((f"Ошибка: Курсы для базовой валюты '{base}' "
                   "не найдены или имеют неверный формат."))
            return 
        total_balance = 0
        print(f'Портфель пользователя c id={user_id} (база: {base}):')
        for currency_code, wallet_data in user_wallets.items():
            balance = wallet_data.get('balance')
            if currency_code in base_currency_rates:
                rate = base_currency_rates[currency_code]['rate']
                balance_base = round(balance / rate, 2)
                total_balance += balance_base
                print(f'- {currency_code}: {balance} -> {balance_base} {base}')
        print('-' * 40)
        print(f'ИТОГО: {total_balance} {base}')


@handle_errors
def buy(user_id: int, currency: str, amount: float):
    """
    Функция для покупки валют.
    """
    validate_currency_code(currency)
    if not isinstance(amount, float):
        raise TypeError('Количество покупаемой валюты должно быть числом.')
    if amount <= 0:
        raise ValueError('Количество покупаемой валюты должно быть больше нуля.')
    portfolios = load_data(PORTFOLIOS_DATA_PATH)
    ids = [portfolio['user_id'] for portfolio in portfolios]
    if user_id not in ids:
        raise ValueError(f'Портфель пользователя с id={user_id} не найден.')
    for portfolio in portfolios:
        if portfolio['user_id'] == user_id:
            if currency not in portfolio['wallets']:
                portfolio['wallets'][currency] = {"balance": 0}
            initial_currency_balance = portfolio['wallets'][currency]['balance']
            rate = get_rate(currency, 'USD')
            if rate:
                currency_price = rate['rate'] * amount
                usd_balance = portfolio['wallets']['USD']['balance']
                if usd_balance >= currency_price:
                    portfolio['wallets']['USD']['balance'] -= currency_price
                    portfolio['wallets'][currency]["balance"] += amount 
                    print((f'Покупка выполнена: {amount} {currency} '
                        f' по курсу {rate.get('rate')} USD\n'))
                    print('Изменения в портфеле:\n')
                    currency_balance = portfolio['wallets'][currency]['balance']
                    print(f'- {currency}: было {initial_currency_balance} -> стало {currency_balance}')
                    print(f'Стоимость покупки: {currency_price} USD')
                else:
                    print((f'Недостаточно средст для покупки валюты {currency}.\n'
                        f'Курс {currency} -> USD: {rate}.\n'
                        f'Для покупки {amount} {currency} необходимо '
                        f'иметь на кошельке {currency_price} USD.\n'
                        f'На вашем балансе: {usd_balance} USD'))
            else:
                print('Ошибка получения курса.')
            break
    save_data(PORTFOLIOS_DATA_PATH, portfolios)


@handle_errors
def add_usd(user_id: int, amount: float):
    """
    Пополняет баланс USD кошелька.
    """
    if not isinstance(user_id, int):
        raise TypeError('Идентификатор пользователя должен быть целым числом.')
    if not isinstance(amount, float):
        raise TypeError('Количество пополняемой валюты должно быть числом.')
    if amount <= 0:
        raise ValueError('Количество пополняемой валюты должно быть положительным.')
    portfolios = load_data(PORTFOLIOS_DATA_PATH)
    for portfolio in portfolios:
        if portfolio['user_id'] == user_id:
            usd_balance_before = portfolio['wallets']['USD']['balance']
            portfolio['wallets']['USD']['balance'] += amount 
            usd_balance_after = portfolio['wallets']['USD']['balance']
            save_data(PORTFOLIOS_DATA_PATH, portfolios)
            return f'Баланс успешно пополнен.\n{usd_balance_before} USD -> {usd_balance_after} USD'


@handle_errors
def sell(user_id: int, currency: str, amount: float):
    """
    Функция для продажи указанной валюты.
    """
    if not isinstance(user_id, int):
        raise TypeError('Идентификатор пользователя должен быть целым числом.')
    validate_currency_code(currency)
    if not isinstance(amount, float):
        raise TypeError('Количество продаваемой валюты должно быть числом.')
    if amount <= 0:
        raise ValueError('Количество продаваемой валюты должно быть положительным.')
    portfolios = load_data(PORTFOLIOS_DATA_PATH)
    ids = [portfolio['user_id'] for portfolio in portfolios]
    if user_id not in ids:
        raise ValueError(f'Портфель пользователя с id={user_id} не найден.')
    for portfolio in portfolios:
        if portfolio['user_id'] == user_id:
            user_wallets = portfolio['wallets']
            if currency in user_wallets:
                currency_balance = user_wallets[currency]['balance']
                if currency_balance >= amount:
                    portfolio['wallets'][currency]['balance'] -= amount 
                    currency_balance_after = portfolio['wallets'][currency]['balance']
                    usd_balance_before = portfolio['wallets']['USD']['balance']
                    rate = get_rate(currency, 'USD')
                    usd_amount = rate['rate'] * amount
                    portfolio['wallets']['USD']['balance'] += usd_amount
                    usd_balance_after = portfolio['wallets']['USD']['balance']
                    save_data(PORTFOLIOS_DATA_PATH, portfolios)
                    return (('Операция продажи прошла успешно!\n'
                    f'{currency_balance} {currency} -> {currency_balance_after} {currency}\n'
                    f'{usd_balance_before} USD -> {usd_balance_after} USD'))
                else:
                    return ((f'У вас недостаточно средств для продажи.\n'
                           f'На счете: {currency_balance}\n.' 
                           f'Необходимо минимум: {amount}'))
            else:
                return ((f'У вас нет кошелька {currency}.\n'
                       'Добавьте валюту: она создается автоматически при первой покупке.'))