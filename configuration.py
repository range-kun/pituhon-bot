import os

MAIN_CHANNEL_ID = 873248515042738176
DB_NAME = "d3lg89is3baabv"
DB_HOST = "ec2-52-211-144-45.eu-west-1.compute.amazonaws.com"
MAX_HIST_RETRIEVE_RECORDS = 10
DEFAULT_TRANSLATE_LANGUAGE = "russian"
PYTHON_BOT_ID = 698973448772386927
TEST_CHANNEL_ID = 698975367326728352
VOTE_TIME = 12  # minutes

try:
    with open('config.txt', 'r') as my_file:
        TOKEN = my_file.readline().strip()
        API_KEY = my_file.readline().strip()
        SEARCH_ENGINE_ID = my_file.readline().strip()
        DB_USER = my_file.readline().strip()
        DB_PASSWORD = my_file.readline().strip()
        
except FileNotFoundError:
    TOKEN = os.environ.get('BOT_TOKEN')
    API_KEY = os.environ.get('API_KEY')
    SEARCH_ENGINE_ID = os.environ.get('SEARCH_ENGINE_ID')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
