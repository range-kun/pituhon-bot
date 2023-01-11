import calendar
from datetime import datetime, timedelta

from discord.channel import TextChannel

from app.log import logger


def is_last_month_day():
    this_day = datetime.now()
    last_month_day = calendar.monthrange(this_day.year, this_day.month)[1]
    return last_month_day == this_day.day


def is_sunday():
    return datetime.today().strftime("%A") == "Sunday"


def yesterday():
    return datetime.date(datetime.now() - timedelta(days=1))


def today():
    return datetime.date(datetime.now())


def fetch_all_channel_users(channel: TextChannel) -> list:
    human_members = [user for user in channel.members if not user.bot]
    return human_members


async def send_yaml_text(text: str, ctx):
    yaml_message_style = str(f"```yaml\n{text}```")
    await ctx.send(yaml_message_style)


def catch_exception(method):
    async def wrapper(cls, *args, **kwargs):
        try:
            result = await method(cls, *args, **kwargs)
        except Exception as e:
            logger.opt(exception=True).error(f"Exception was caught in {method.__qualname__}: " + str(e))
        else:
            return result
    return wrapper
