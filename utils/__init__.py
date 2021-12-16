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
