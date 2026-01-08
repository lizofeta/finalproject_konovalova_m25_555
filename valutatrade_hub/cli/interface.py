from valutatrade_hub.core.currencies import initialize_currencies
from valutatrade_hub.core.exceptions import ValutatradeError
from valutatrade_hub.core.usecases import (
    PortfolioCommands,
    RatesCommands,
    Session,
    UserCommands,
)
from valutatrade_hub.core.utils import Utils
from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.scheduler import RatesScheduler
from valutatrade_hub.parser_service.updater import RatesUpdater


class CLI:
    def __init__(self):
        self.session = Session()
        self.user_commands = UserCommands(self.session)
        self.portfolio_commands = PortfolioCommands(self.session)
        self.rates_commands = RatesCommands()
        self.utils = Utils()
        self.parser_config = ParserConfig()
        self.rates_updater = RatesUpdater(self.parser_config)
        self.scheduler = RatesScheduler(self.rates_updater, 300)
        self.active = True 

    def run(self):
        # Инициализация реестра валют
        initialize_currencies()
        # Настройка логирования
        setup_logging()
        # Запуск автообновления курсов
        self.scheduler.start()

        print('Добро пожаловать на платформу для '
              ' отслеживания и симуляции торговли валютами!')
        print('-' * 50)
        print('Доступные команды: ')
        print('\n'.join(self.utils.help()))
        print()
        print('ВНИМАНИЕ! Во время регистрации необходимо '
              'совершить пополнение USD-кошелька. Кошелек создается '
              'автоматически при первой покупке валюты.\n')

        while self.active:
            try:
                print('\nВведите команду: ')
                user_input = input('> ')
                # Парсинг команды:
                parsed_input = self.utils.parse_user_input(user_input)
                command = (parsed_input.get('command')).lower()
                args = parsed_input.get('args')

                match command:
                    case 'help':
                        print('\n'.join(self.utils.help()))
                    case 'exit':
                        print('\nДо свидания!')
                        self.scheduler.stop()
                        self.active = False
                    case 'register':
                        # Валидация ввода
                        self.utils.validate_command(command, args)
                        # Регистрация
                        username = args[0]
                        password = args[1]
                        initial_usd_amount = float(args[2])
                        print(self.user_commands\
                              .register(username, password, initial_usd_amount))
                    case 'login':
                        # Валидация ввода
                        self.utils.validate_command(command, args)
                        # Вход
                        if self.session.is_logged_in():
                            username = self.session.get_current_user().username
                            print(f'Вы уже в системе под именем {username}')
                            continue
                        username = args[0]
                        password = args[1]
                        print(self.user_commands.login(username, password))
                    case 'logout':
                        # Выход из аккаунта 
                        if not self.session.is_logged_in():
                            print('Вы не вошли в систему, чтоб из нее выходить.')
                            continue
                        self.session.logout()
                        if not self.session.is_logged_in():
                            print('Вы успешно вышли из системы.')
                    case 'show-portfolio':
                        # Показываем портфель
                        base = args[0] or 'USD'
                        print(self.portfolio_commands.show_portfolio(base))
                    case 'buy':
                        # Валидация ввода
                        self.utils.validate_command(command, args)
                        # Покупка валюты
                        currency = args[0]
                        amount = float(args[1])
                        print(self.portfolio_commands.buy(currency, amount))
                    case 'buy-usd':
                        # Валидация ввода
                        self.utils.validate_command(command, args)
                        # Пополнение usd кошелька
                        amount = float(args[0])
                        print(self.portfolio_commands.buy_usd(amount))
                    case 'sell':
                        # Валидация ввода
                        self.utils.validate_command(command, args)
                        # Продажа валюты
                        currency = args[0]
                        amount = float(args[1])
                        print(self.portfolio_commands.sell(currency, amount))
                    case 'get-rate':
                        # Валидация ввода
                        self.utils.validate_command(command, args)
                        # Получение курса
                        currency_from = args[0]
                        currency_to = args[1]
                        print(self.rates_commands.get_rate(currency_from, currency_to))
                    case 'update-rates':
                        # Валидация ввода
                        self.utils.validate_command(command, args)
                        # Запуск обновления курсов
                        source = None
                        base = 'USD'
                        if args:
                            if args[0] == 'coingecko' or args[0] == 'exchangerate':
                                source = args[0]
                                base = args[1] if len(args) > 1 else 'USD'
                            else:
                                base = args[0]
                        self.rates_updater.run_update(source, base)
                        print('Курсы успешно обновлены.')
                    case 'show-rates':
                        # Валидация ввода
                        self.utils.validate_command(command, args)
                        currency = None 
                        top = None 
                        base = 'USD'
                        # Заполнение параметров
                        if args:
                            if args[0].lower() == 'top':
                                top = int(args[1])
                                base = args[2] if len(args) > 2 else 'USD'
                            else:
                                currency = args[0]
                                base = args[1] if len(args) > 1 else 'USD'
                        # Запуск функции
                        print(self.rates_commands.show_rates(currency, top, base))
                    case '_':
                        print('Неизвестная команда. Используйте команду help, '
                              'чтоб ознакомиться со всеми доступными командами.')
                        continue

            except ValueError as e:
                print(e)
            except TypeError as e:
                print(e)
            except ValutatradeError as e:
                print(e)
            except KeyboardInterrupt:
                self.scheduler.stop()
            except Exception as e:
                self.scheduler.stop()
                print(f'Произошла непредвиденная ошибка: {e}')

def main():
    """ Точка входа в CLI """
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()