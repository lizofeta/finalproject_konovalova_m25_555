import logging
from functools import wraps

logger = logging.getLogger(__name__)

def format_log(
        action:str,
        username:str,
        currency:str = None,
        amount:float = None,
        rate:float = None,
        base:str = None,
        result:str = 'OK',
        error_type:str = None,
        error_message:str = None,
        verbose:dict = None
):
    """
    Функция для форматирования логов

    Аргументы: 
        action:str - название операции (BUY | BUY_USD |SELL | LOGIN | REGISTER)
        username:str - имя пользователя
        currency:str - код валюты
        amount:float - количество продаваемой/покупаемой валюты
        rate:float - аткуальный курс для пары валют
        base:str - базовая валюта
        result:str - результат операции (OK/ERROR)
        error_type:str - тип ошибки
        error_message:str - сообщение об ошибке
        verbose:dict - дополнительный контекст (н-р: состояние кошелька)
    
    Возвращает: 
        Отформатированное сообщение для логирования
    """
    parts = [
        f"{action}"
    ]

    if username:
        parts.append(f"username='{username}'")

    if currency:
        parts.append(f"currency='{currency}'")
    if amount:
        parts.append(f"amount={amount}")
    if rate:
        parts.append(f"rate={rate}")
    if base:
        parts.append(f"base='{base}'")
    
    parts.append(f"result='{result}'")

    if error_type:
        parts.append(f"error_type='{error_type}'")
    if error_message:
        parts.append(f"error_message='{error_message}'")
    if verbose:
        for key, value in verbose.items():
            parts.append(f"{key}: {value}")
    
    return " ".join(parts)

    

def log_action(action:str, verbose:bool = False):
    """
    Фабрика декораторов с парамметрами:
        action: sell | buy | register | login
        verbose: доп. информация о действии (баланс: было/стало)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            username = None
            rate = None
            currency_code = None
            amount = None
            base = 'USD'
            
            # Извлекаем информацию о пользователе 
            self_obj = args[0] if args else None
            if self_obj and hasattr(self_obj, "session"):
                current_user = getattr(self_obj.session, "current_user", None)
                if current_user:
                    username = getattr(current_user, "username", None)
                    user_id = getattr(current_user, "user_id", None)
            
            # Извлекаем параметры функции
            # buy/sell
            if action in ['SELL', 'BUY', 'BUY_USD']:
                if action == 'BUY_USD':
                    currency_code = 'USD'
                    amount = args[1]
                else:
                    currency_code = args[1] 
                    amount = args[2]
            # login/register
            if action in ['REGISTER', 'LOGIN']:
                username = args[1]
                if action == 'REGISTER':
                    amount = args[3]
            
            verbose_context = {}

            # Пытаемся получить информацию о состоянии кошелька до операции
            if verbose and action in ['SELL', 'BUY', 'BUY_USD']:
                if self_obj and hasattr(self_obj, "database"):
                    try:
                        portfolio = self_obj\
                            .database.find_portfolio_by_user_id(user_id)
                        if portfolio and currency_code:
                            wallet = portfolio.get_wallet(currency_code)
                            if wallet:
                                verbose_context['balance_before'] = (
                                    f"{wallet.balance:.4f}"
                                )
                            else:
                                verbose_context['balance_before'] = 0
                    except Exception:
                        pass
            
            try:
                # Выполнение функции
                result = func(*args, **kwargs)

                # Пытаемся получить курс
                if (
                    action in ['BUY', 'SELL'] 
                    and self_obj 
                    and hasattr(self_obj, "database")
                ):
                    try:
                        rate = self_obj.database.get_rate(currency_code, base)
                    except Exception:
                        pass
                
                # Получаем состояние счета после операции
                if (
                    verbose_context 
                    and verbose 
                    and action in ['SELL', 'BUY', 'BUY_USD']
                ):
                    if self_obj and hasattr(self_obj, "database"):
                        try:
                            portfolio = self_obj\
                                .database.find_portfolio_by_user_id(user_id)
                            if portfolio:
                                wallet = portfolio\
                                    .get_wallet(currency_code)
                                if wallet:
                                    verbose_context['balance_after'] = (
                                        f"{wallet.balance:.4f}"
                                    )
                        except Exception:
                            pass
                
                logger.info(
                    format_log(
                        action=action,
                        username=username,
                        currency=currency_code,
                        amount=amount,
                        rate=rate,
                        base=base,
                        verbose=verbose_context,
                        result='OK'
                    )
                )

                return result
            
            except Exception as e:
                logger.info(
                    format_log(
                        action,
                        username,
                        currency_code,
                        amount,
                        rate,
                        base,
                        result='ERROR',
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
                )
                raise
        return wrapper 
    return decorator 