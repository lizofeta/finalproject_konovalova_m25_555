from functools import wraps

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            print(f'Файл не найден: {e}')
            return None
        except KeyError as e:
            print(f'Ошибка ключа: {e}')
            return None
        except ValueError as e:
            print(f'Ошибка валидации: {e}')
            return None
        except TypeError as e:
            print(f'Ошибка типа: {e}')
            return None
        except Exception as e:
            print(f'Произошла непредвиденная ошибка: {e}')
            return None
    return wrapper