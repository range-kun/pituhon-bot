import os

try:
    with open('config.txt', 'r') as myfile:
        TOKEN = myfile.readline().strip()
        API_KEY = myfile.readline().strip()
        SEARCH_ENGINE_ID = myfile.readline().strip()
        DB_USER = myfile.readline().strip()
        DB_PASSWORD = myfile.readline().strip()
except:
    token = os.environ.get('BOT_TOKEN')
    API_KEY = os.environ.get('API_KEY')
    SEARCH_ENGINE_ID = os.environ.get('SEARCH_ENGINE_ID')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')