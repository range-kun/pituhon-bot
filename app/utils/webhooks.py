from __future__ import annotations

import hashlib

import aiohttp
from discord import TextChannel, Webhook, NotFound, Embed
from discord.ext.commands import Bot

from app import TOKEN
from app.configuration import SECRET_KEY
from app.utils import redis_connection_manager


def fetch_web_hook_url(token_hash: str) -> str | None:
    with redis_connection_manager() as redis_connection:
        return redis_connection.get(token_hash)


def set_web_hook_url(url: str, token_hash: str):
    with redis_connection_manager() as redis_connection:
        redis_connection.set(token_hash, url)


def get_token_hash(input_string, hash_algorithm="sha256") -> str:
    hash_object = hashlib.new(hash_algorithm)

    input_bytes = input_string.encode('utf-8')
    salt_bytes = SECRET_KEY.encode('utf-8')

    combined_bytes = input_bytes + salt_bytes
    hash_object.update(combined_bytes)
    hashed_string = hash_object.hexdigest()

    return hashed_string


async def verify_url(url: str, channel: TextChannel, bot: Bot) -> bool:
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(url, session=session)
    try:
        webhook = await bot.fetch_webhook(webhook.id)  # to fetch all info
    except NotFound:
        return False
    if webhook.auth_token == TOKEN and webhook.channel == channel:
        return True
    return False


class WebHookSender:

    def __init__(self):
        self.webhook_url = self.fetch_webhook_url()

    async def send_data(self, **kwargs):
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(self.webhook_url, session=session)
            await webhook.send(**kwargs)

    @staticmethod
    def fetch_webhook_url() -> str | None:
        token_hash = get_token_hash(TOKEN)
        url = fetch_web_hook_url(token_hash)
        return url


webhook_sender = WebHookSender()
