from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta

import redis
from discord import Member
from discord.channel import TextChannel
from discord.ext import commands

from app.configuration import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from app.log import logger


class BotSetter:
    bot = None

    def set_bot(self, bot):
        self.bot = bot


def yesterday() -> datetime.date:
    return datetime.date(datetime.now() - timedelta(days=1))


def today() -> datetime.date:
    return datetime.date(datetime.now())


def tomorrow_text_type() -> str:
    return today().strftime("%Y-%m-%d")


def fetch_all_channel_users(channel: TextChannel) -> list[Member]:
    human_members = [user for user in channel.members if not user.bot]
    return human_members


async def send_yaml_text(text: str, ctx: commands.Context):
    yaml_message_style = str(f"```yaml\n{text}```")
    await ctx.send(yaml_message_style)


def catch_exception(method):
    async def wrapper(cls, *args, **kwargs):
        try:
            result = await method(cls, *args, **kwargs)
        except Exception as e:
            logger.opt(exception=True).error(
                f"Exception was caught in {method.__qualname__}: " + str(e),
            )
        else:
            return result

    return wrapper


@contextmanager
def redis_connection_manager(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD):
    connection = redis.Redis(host=host, port=port, password=password, decode_responses=True)
    try:
        yield connection
    finally:
        connection.close()
