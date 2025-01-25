import asyncio
from enum import Enum

from celery import Celery
from celery.schedules import crontab

from app.cogs.birthday_reminder import birthday_reminder
from app.configuration import REDIS_HOST, REDIS_PORT, TIME_ZONE
from app.utils.message_stats_routine import message_day_counter
from app.utils.message_stats_routine.chanel_stats_routine import channel_stats
from app.utils.message_stats_routine.user_stats_routine import user_stats

redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

app = Celery("tasks", broker=redis_url)
app.conf.timezone = TIME_ZONE
app.conf.enable_utc = False
app.conf.worker_concurrency = 1


class TimePeriod(Enum):
    day = "day"
    week = "week"
    month = "month"


@app.task
def user_stats_wrapper(period: str):
    if period == TimePeriod.day.value:
        asyncio.run(user_stats.daily_routine())
    elif period == TimePeriod.week.value:
        asyncio.run(user_stats.weekly_routine())
    elif period == TimePeriod.month.value:
        asyncio.run(user_stats.monthly_routine())


@app.task
def channel_stats_wrapper(period: TimePeriod):
    if period == TimePeriod.day.value:
        asyncio.run(channel_stats.daily_routine())
    elif period == TimePeriod.week.value:
        asyncio.run(channel_stats.weekly_routine())
    elif period == TimePeriod.month.value:
        asyncio.run(channel_stats.monthly_routine())


@app.task
def utils_daily_wrapper(scope: str):
    if scope == "clear":
        asyncio.run(message_day_counter.delete_redis_info())
    elif scope == "birthday":
        asyncio.run(birthday_reminder.remind_birthday_routine())


app.conf.beat_schedule = {
    "user_stats_daily_routine": {
        "task": "app.tasks.user_stats_wrapper",
        "schedule": crontab(hour="02", minute="00"),
        "args": (TimePeriod.day.value,),
    },
    "user_stats_weekly_routine": {
        "task": "app.tasks.user_stats_wrapper",
        "schedule": crontab(hour="02", minute="01", day_of_week="monday"),
        "args": (TimePeriod.week.value,),
    },
    "user_stats_monthly_wrapper": {
        "task": "app.tasks.user_stats_wrapper",
        "schedule": crontab(hour="02", minute="02", day_of_month="1"),
        "args": (TimePeriod.month.value,),
    },
    "channel_stats_daily_routine": {
        "task": "app.tasks.channel_stats_wrapper",
        "schedule": crontab(hour="02", minute="03"),
        "args": (TimePeriod.day.value,),
    },
    "channel_stats_weekly_routine": {
        "task": "app.tasks.channel_stats_wrapper",
        "schedule": crontab(hour="02", minute="04", day_of_week="monday"),
        "args": (TimePeriod.week.value,),
    },
    "channel_stats_monthly_routine": {
        "task": "app.tasks.channel_stats_wrapper",
        "schedule": crontab(hour="02", minute="05", day_of_month="1"),
        "args": (TimePeriod.month.value,),
    },
    "delete_redis_info_routine": {
        "task": "app.tasks.utils_daily_wrapper",
        "schedule": crontab(hour="02", minute="06"),
        "args": ("clear",),
    },
    "send_birthday_info": {
        "task": "app.tasks.utils_daily_wrapper",
        "schedule": crontab(hour="02", minute="07"),
        "args": ("birthday",),
    },
}
