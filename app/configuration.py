from __future__ import annotations

import os

import discord
from decouple import config

PREFIX = "?"
MAX_HIST_RETRIEVE_RECORDS = 10
VOTE_TIME = 20  # minutes
DEFAULT_TRANSLATE_LANGUAGE = "russian"
TEST_CHANNEL_ID = config("TEST_CHANNEL_ID", default=0, cast=int)
MAIN_CHANNEL_ID = config("MAIN_CHANNEL_ID", default=0, cast=int)
SERVER_ID = config("SERVER_ID", cast=int, default=0)
MY_GUILD = discord.Object(id=SERVER_ID)
UMBRA_ID = config("UMBRA_ID", default=0, cast=int)
DEBUG = config("DEBUG", default=False, cast=bool)
SECRET_KEY = config("SECRET_KEY", default="test_secret_key")


# Discord token
TOKEN = config("BOT_TOKEN")
TEST_TOKEN = config("BOT_TEST_TOKEN", default=None)

# Google
API_KEY = config("API_KEY")
SEARCH_ENGINE_ID = config("SEARCH_ENGINE_ID")


# DB
def get_default_db_host() -> str:
    if os.name == "nt":
        return "localhost"
    else:
        return "0.0.0.0"


DB_USER = config("DB_USER", "postgres")
DB_PASSWORD = config("DB_PASSWORD", "postgres")
DB_NAME = config("DB_NAME", "postgres")
DB_HOST = config("DB_HOST", default=get_default_db_host())
DB_PORT = config("DB_PORT", cast=int, default=5432)


# Redis
REDIS_HOST = config("REDIS_HOST", default="redis")
REDIS_PORT = config("REDIS_PORT", default="6379")


LOGGER_OUTPUT = config("LOGGER_OUTPUT", default="std_err")
# std_err if suppose to be written to console
# container if it supposes to work in docker_compose
