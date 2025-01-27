from __future__ import annotations

import hashlib

import aiohttp
from discord import NotFound, TextChannel, Webhook
from discord.ext.commands import Bot
from loguru import logger

from app import TOKEN
from app.configuration import SECRET_KEY
from app.utils import redis_connection_manager


def fetch_web_hook_url(token_hash: str) -> str | None:
    with redis_connection_manager() as redis_connection:
        return redis_connection.get(token_hash)


def set_web_hook_url(url: str, token_hash: str):
    with redis_connection_manager() as redis_connection:
        logger.debug(f"Attempt to set webhook with next token_hash: {token_hash}")
        redis_connection.set(token_hash, url)
        logger.info(f"Web hook set with url {url}")


def get_token_hash(input_string, hash_algorithm="sha256") -> str:
    hash_object = hashlib.new(hash_algorithm)

    input_bytes = input_string.encode("utf-8")
    salt_bytes = SECRET_KEY.encode("utf-8")

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
        if not self.webhook_url:
            logger.error("Cannot send data: Webhook URL is not set.")
            return
        try:
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(self.webhook_url, session=session)
                await webhook.send(**kwargs)
        except Exception as e:
            logger.exception(f"Failed to send data via webhook: {e}")

    @staticmethod
    def fetch_webhook_url() -> str | None:
        logger.info("Fetching webhook URL...")
        try:
            token_hash = get_token_hash(TOKEN)
            logger.debug(f"Generated token hash: {token_hash}")
            url = fetch_web_hook_url(token_hash)
            if url:
                logger.info("Webhook URL fetched successfully.")
            else:
                logger.warning("No webhook URL found in the database.")
            return url
        except Exception as e:
            logger.exception(f"Error while fetching webhook URL: {e}")
            return None


webhook_sender = WebHookSender()
