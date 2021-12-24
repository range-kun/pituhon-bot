import calendar
from datetime import datetime, timedelta


def is_last_month_day():
    this_day = datetime.now()
    last_month_day = calendar.monthrange(this_day.year, this_day.month)[0]
    return last_month_day == this_day.day


def yesterday():
    return datetime.date(datetime.now() - timedelta(days=1))


def today():
    return datetime.date(datetime.now())


def catch_exception(method):
    async def wrapper(cls, *args, **kwargs):
        try:
            result = await method(cls, *args, **kwargs)
        except Exception as e:
            print(f"Поймано исключение в методе {method.__qualname__}: " + str(e))
        else:
            return result
    return wrapper
