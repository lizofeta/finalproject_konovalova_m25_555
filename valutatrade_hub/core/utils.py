# Модуль для вспомогательных команд

import shlex

from valutatrade_hub.core.exceptions import ArgumentsError, CommandNotAllowedError


class Utils:
    def __init__(self):
        self.allowed_commands = [
            'register',
            'login',
            'logout',
            'show-portfolio',
            'buy',
            'buy-usd',
            'sell',
            'get-rate',
            'update-rates',
            'show-rates',
            'help',
            'exit'
        ]
    
    def help(self):
        """ Возвращает доступные команды """
        return [
'register <username> <password> <initial_usd_amount>   -> зарегистрироваться на платформе.', # noqa: E501
'login <username> <password>                           -> выполнить вход в свой аккаунт.', # noqa: E501
'logout                                                -> выйти из своего аккаунта.', # noqa: E501
'show-portfolio <base>                                 -> показать все свои кошельки и итоговую стоимость в базовой валюте.', # noqa: E501
'buy <currency> <amount>                               -> купить валюту.', # noqa: E501
'buy-usd <amount>                                      -> пополнить USD кошелек.', # noqa: E501
'sell <currency> <amount>                              -> продать валюту.', # noqa: E501
'get-rate <from_currency> <to_currency>                -> получить текущий курс одной валюты к другой.', # noqa: E501
'update-rates <source> (ciongecko/exchangerate) <base> -> обновить курсы. Если источник не указан - обновляются все.', # noqa: E501
'show-rates <currency> <base>                          -> показать курс для указанной валюты по отношению к базовой.', # noqa: E501
'show-rates <top N> <base>                             -> показать N самых дорогих криптовалют по отношению к базовой.', # noqa: E501
'help                                                  -> посмотреть список доступных команд (данное сообщение).', # noqa: E501
'exit                                                  -> выйти из приложения.', # noqa: E501
'\nБазовая валюта по умолчанию - USD.',
'\nДоступные фиатные валюты: USD, RUB, EUR, IRR, GBP, KZT, CNY',
'Доступные криптовалюты: BTC, ETH, SOL'
        ]
    
    def parse_user_input(self, user_input:str):
        """ 
        Парсит введенную пользователем команду 
        
        Аргументы:
            user_input:str - полная команда пользователя

        Возвращает:
            command - команда (название)
            args - аргументы

        Выбрасывает:
            CommandNotAllowedError,
            ArgumentsError
        """
        if not isinstance(user_input, str):
            raise TypeError('Команда должна быть строкой.')
        if not user_input:
            return ''
        user_input = shlex.split(user_input)
        command = user_input[0]
        args = user_input[1:]

        if command not in self.allowed_commands:
            raise CommandNotAllowedError(command)
        
        if not args and command not in \
            ['logout', 'help', 'exit', 'show-portfolio', 'update-rates']:
            raise ArgumentsError(command)
        
        return {'command': command, 'args': args}
    
    def validate_command(self, command:str, args:str):
        """ 
        Метод для вадидации команд 
        
        Аргументы:
            command:str - команда
            args:str - аргументы
        
        Выбрасывает:
            ArgumentsError,
            ValueError
        """
        match command:
            case 'register':
                if len(args) != 3:
                    raise ArgumentsError(command,\
                         'register <username> <password> <initial_usd_amount>')
                try:
                    args[2] = float(args[2])
                except ValueError as e:
                    raise ValueError\
                    ('Количество покупаемой валюты должно быть числом.') from e
            case 'login':
                if len(args) != 2:
                    raise ArgumentsError(command, 'login <username> <password>')
            case 'buy':
                if len(args) != 2:
                    raise ArgumentsError(command, 'buy <currency> <amount>')
                try:
                    args[1] = float(args[1])
                except ValueError as e:
                    raise ValueError\
                    ('Количество покупаемой валюты должно быть числом.') from e
            case 'buy-usd':
                if len(args) != 1:
                    raise ArgumentsError(command, 'buy-usd <amount>')
                try:
                    args[0] = float(args[0])
                except ValueError as e:
                    raise ValueError\
                    ('Количество покупаемой валюты должно быть числом.') from e
            case 'sell':
                if len(args) != 2:
                    raise ArgumentsError(command, 'sell <currency> <amount>')
                try:
                    args[1] = float(args[1])
                except ValueError as e:
                    raise ValueError\
                    ('Количество продаваемой валюты должно быть числом.') from e
            case 'get-rate':
                if len(args) != 2:
                    raise ArgumentsError\
                    (command, 'get-rate <from_currency> <to_currency>')
            case 'show-rates':
                if len(args) > 3:
                    raise ArgumentsError\
                    (command, 
                     'show-rates <currency> <base> / '
                     'show-rates <top N> <base>')
                if args[0] == 'top':
                    try:
                        args[1] = int(args[1].strip())
                    except ValueError as e:
                        raise ValueError\
                        ('Количество топ-криптовалют должно быть целым числом.') from e
            case 'update-rates':
                if len(args) > 2:
                    raise ArgumentsError\
                    (command, 'update-rates <source> (coingecko/exchangerate) <base>')