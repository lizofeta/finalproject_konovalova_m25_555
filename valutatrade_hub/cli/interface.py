from valutatrade_hub.core.usecases import (
    register,
    login,
    show_portfolio,
    buy,
    add_usd,
    sell,
    get_rate   
)
import shlex

current_user_id = None

def help():
    """ Показывает доступные команды """
    print("\nДоступные команды:")
    print("  register <username> <password> <initial_amount>   - Зарегистрировать нового пользователя.")
    print("  login <username> <password>                       - Войти в систему.")
    print("  logout                                            - Выйти из системы.")
    print("  show-portfolio                                    - Показать свой портфель.")
    print("  buy <currency> <amount>                           - Купить валюту.")
    print("  add-usd <amount>                                  - Пополнить кошелек USD.")
    print("  sell <currency> <amount>                          - Продать валюту.")
    print("  get-rate <from_currency> <to_currency>            - Получить курс валюты.")
    print("  help                                              - Показать доступные команды.")
    print("  exit                                              - Выйти из программы.")
    print("\nДля команд buy/sell/show-portfolio/logout вы должны быть залогинены.")
    print('При регистрации нужно сразу пополнить кошелек в валюте USD.')

def run_cli():
    print('Добро пожаловать на платформу для отслеживания и симуляции торговли валютами!')
    print('Для просмотра списка доступных команд введите "help"')
    global current_user_id
    while True:
        command_line = input('\nВведите команду: ')
        if not command_line.strip():
            continue
        command_parts = shlex.split(command_line)
        command = command_parts[0].lower()
        args = command_parts[1:]

        match command:
            case 'help':
                help()
            case 'exit':
                print('\nДо свидания!')
                break 
            case 'register':
                if len(args) != 3:
                    print(('Неверный ввод команды.\n'
                    'Попробуйте снова: register <username> <password> <initial_amount>'))
                    continue
                username = args[0]
                password = args[1]
                initial_amount = float(args[2])
                result = register(username, password, initial_amount)
                if result:
                    print(result)
            case 'login':
                if len(args) != 2:
                    print(('Неверный ввод команды.\n'
                    'Попробуйте снова: login <username> <password>'))
                    continue
                if not current_user_id:
                    username = args[0]
                    password = args[1]
                    result = login(username, password)
                    if result:
                        success = result['login_state']
                        if success:
                            print('Вы успешно вошли в систему.')
                            current_user_id = int(result['user_id'])
                        else:
                            print(f'Неверный пароль для пользователя {username}.')
                    else:
                        print('Во время авторизации произошла ошибка.')
                else:
                    print((f'Вы уже авторизованы в акаунте с id={current_user_id}.\n'
                           'Чтобы выйти, введите команду logout'))
            case 'logout':
                if current_user_id:
                    print('Выполняю выход из системы.')
                    current_user_id = None
                else:
                    print(('Вы не вошли в систему.\n'
                    'Войдите, используя команду login <username> <password>'))
            case 'show-portfolio':
                if current_user_id:
                    show_portfolio(current_user_id)
                else:
                    print(('Вы не авторизованы в системе.\n'
                    'Войдите, используя команду login <username> <password>'))
            case 'buy':
                if not current_user_id:
                    print(('Вы не авторизованы в системе.\n'
                    'Войдите, используя команду login <username> <password>'))
                    continue
                if len(args) != 2:
                    print(('Неверный ввод команды.\n'
                    'Попробуйте снова: buy <currency> <amount>'))
                    continue
                currency = args[0]
                amount = float(args[1])
                buy(current_user_id, currency, amount)
            case 'add-usd':
                if not current_user_id:
                    print(('Вы не авторизованы в системе.\n'
                    'Войдите, используя команду login <username> <password>'))
                    continue
                if len(args) != 1:
                    print(('Неверный ввод команды.\n'
                    'Попробуйте снова: add-usd <amount>'))
                    continue
                amount = float(args[0])
                result = add_usd(current_user_id, amount)
                if result:
                    print(result)
            case 'sell':
                if not current_user_id:
                    print(('Вы не авторизованы в системе.\n'
                    'Войдите, используя команду login <username> <password>'))
                    continue
                if len(args) != 2:
                    print(('Неверный ввод команды.\n'
                    'Попробуйте снова: sell <currency> <amount>'))
                    continue
                currency = args[0]
                amount = float(args[1])
                if currency == 'USD':
                    print('Продажа USD валюты недопустима.')
                    continue
                result = sell(current_user_id, currency, amount)
                if result:
                    print(result)
            case 'get-rate':
                if len(args) != 2:
                    print(('Неверный ввод команды.\n'
                    'Попробуйте снова: get-rate <from_currency> <to_currency>'))
                    continue
                from_currency = args[0]
                to_currency = args[1]
                rates = get_rate(from_currency, to_currency)
                if rates:
                    direct_rate = rates.get('rate')
                    reversed_rate = rates.get('reversed_rate')
                    updated_at = rates.get('updated_at')
                    print(f'Курс {from_currency}->{to_currency}: {direct_rate}')
                    print(f'Обратный курс {to_currency}->{from_currency}: {reversed_rate}')
                    print(f'Обновлено: {updated_at}')
            case _:
                print(('Неизвестная команда.\n'
                'Введите help для просмотра доступных команд.'))