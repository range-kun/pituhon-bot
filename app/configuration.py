import os

from decouple import config
import discord

PREFIX = "?"
MAX_HIST_RETRIEVE_RECORDS = 10
DEFAULT_TRANSLATE_LANGUAGE = "russian"
PYTHON_BOT_ID = 698973448772386927
TEST_CHANNEL_ID = 698975367326728352
MAIN_CHANNEL_ID = 873248515042738176
VOTE_TIME = 60  # minutes
UMBRA_ID = 439474652079718410
SERVER_ID = 698975228323168266
MY_GUILD = discord.Object(id=SERVER_ID)


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
