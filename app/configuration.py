import os

import discord
from decouple import config

PREFIX = "?"
MAX_HIST_RETRIEVE_RECORDS = 10
VOTE_TIME = 60  # minutes
DEFAULT_TRANSLATE_LANGUAGE = "russian"
TEST_CHANNEL_ID = config("TEST_CHANNEL_ID", default=0, cast=int)
MAIN_CHANNEL_ID = config("MAIN_CHANEL_ID", default=0, cast=int)
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
DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")
DB_NAME = config("DB_LOCAL_NAME")

if os.name == "nt":
    default_host = "localhost"
else:
    default_host = "0.0.0.0"
DB_HOST = config("DB_HOST", default=default_host)


# Redis
REDIS_PASSWORD = config("REDIS_PASSWORD")
REDIS_HOST = config("REDIS_HOST")
REDIS_PORT = config("REDIS_PORT")


LOGGER_OUTPUT = config("LOGGER_OUTPUT", default="std_err")
# std_err if suppose to be written to console
# container if it suppose to work in docker_compose
