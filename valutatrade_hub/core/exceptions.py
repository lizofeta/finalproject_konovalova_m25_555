class ValutatradeError(Exception):
    """ Базовое исключение для пользовательских исключений """
    pass

class NoContentError(ValutatradeError):
    """ Исключение, возникающее при отсутствии контента в файле / его части """
    def __init__(self, filepath):
        self.filepath = filepath
        message = ((f'Не удалось загрузить контент из файла {filepath}.\n'
                   'Возможно, запрашиваемая информация отсутствует.'))
        super().__init__(message)

class CurrencyNotFoundError(ValutatradeError):
    """ Исключение, возникающее при отсутствии валюты в реестре валют """
    def __init__(self, code:str):
        self.code = code 
        message = f"Валюта с кодом {self.code} отсутствует в реестре валют."
        super().__init__(message)

class InsufficientFundsError(ValutatradeError):
    """ 
    Исключение, возникающее, если на кошельке недостаточно средств 
    для снятия / покупки другой валюты.

    Атрибуты:
        available:float - доступно средств на балансе
        required:float - необходимо средств для проведения операции
        code:str - код валюты, которой проводится операция
    """
    def __init__(self, available:float, code:str, required:float):
        self.available = available
        self.code = code 
        self.required = required
        message = f"Недостаточно средств: доступно {self.available}\
              {self.code}, требуется {self.required} {self.code}"
        super().__init__(message)

class ApiRequestError(ValutatradeError):
    """
    Исключение, возникающее при возникновении ошибке при подключении к внешнему API

    Аргументы:
        reason:str - причина ошибки
    """
    def __init__(self, reason:str):
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {self.reason}"
        super().__init__(message)

class UsernameAlreadyTakenError(ValutatradeError):
    """
    Исключение, возникающее, если при регистрации имя пользователя уже занято
    """
    def __init__(self, username:str):
        self.username = username
        message = f"Имя пользователя '{self.username}' занято."
        super().__init__(message)

class UserNotFoundError(ValutatradeError):
    """
    Исключение, возникающее, если не был найден в базе данных заданный пользователь.
    """
    def __init__(self, username:str):
        self.username = username 
        message = f"Пользователь с именем '{self.username}' не был найден."
        super().__init__(message)

class ShortPasswordError(ValutatradeError):
    """
    Исключение, возникающее при возникновении попытки 
    создать слишком короткий пароль.
    """
    def __init__(self):
        super().__init__("Пароль должен быть не короче 4-х символов.")

class WrongPasswordError(ValutatradeError):
    """
    Исключение, возникающее при неправильно введенном пароле 
    при входе в систему.
    """
    def __init__(self):
        super().__init__("Введен неверный пароль.")

class UserUnlogedError(ValutatradeError):
    """
    Исключение, возникающее, если пользователь не залогинен.
    """
    def __init__(self):
        super().__init__("Необходимо сначала войти в систему.")

class RateUnavailableError(ValutatradeError):
    """
    Исключение, возникающее при ошибке получения курса
    """
    def __init__(self, currency_from:str, currency_to:str):
        self.currency_from = currency_from 
        self.currency_to = currency_to
        super().__init__(f"Ошибка получения курса\
                          для {self.currency_from}->{self.currency_to}")

class CommandNotAllowedError(ValutatradeError):
    """
    Исключение, возникающее, если пользователь вводит неподдерживаемую команду
    """
    def __init__(self, command:str):
        super().__init__(f"Команда {command} не поддерживается в приложении.")

class ArgumentsError(ValutatradeError):
    """
    Исключение, возникающее при введении неверных агрументов команды
    """
    def __init__(self, command:str, prompt:str=None):
        if prompt:
            message = f"Неверный ввод команды {command}.\
                 Попробуйте снова: {prompt}"
        else:
            message = f"Неверный ввод команды {command}.\
                Воспользуйтесь командой help и попробуйте снова."
        super().__init__(message)