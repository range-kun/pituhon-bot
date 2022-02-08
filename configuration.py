import os
import yaml

DB_NAME = "d3lg89is3baabv"
DB_HOST = "ec2-52-211-144-45.eu-west-1.compute.amazonaws.com"
MAX_HIST_RETRIEVE_RECORDS = 10
DEFAULT_TRANSLATE_LANGUAGE = "russian"
PYTHON_BOT_ID = 698973448772386927
TEST_CHANNEL_ID = 698975367326728352
MAIN_CHANNEL_ID = 873248515042738176
VOTE_TIME = 60  # minutes
REDIS_HOST = "redis-17886.c293.eu-central-1-1.ec2.cloud.redislabs.com"
REDIS_PORT = 17886

try:
    with open('config.yaml', 'r') as my_file:
        secret_configs = yaml.safe_load(my_file)
except FileNotFoundError:
    secret_configs = os.environ
    
TOKEN = secret_configs.get('BOT_TOKEN')
API_KEY = secret_configs.get('API_KEY')
SEARCH_ENGINE_ID = secret_configs.get('SEARCH_ENGINE_ID')
DB_USER = secret_configs.get('DB_USER')
DB_PASSWORD = secret_configs.get('DB_PASSWORD')
REDIS_PASSWORD = secret_configs.get('REDIS_PASSWORD')
