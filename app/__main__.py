import sys

from app import configuration, log
from app.bot import bot

if __name__ == "__main__":
    mode = sys.argv[1]
    TOKEN = configuration.TOKEN
    if mode == "test" and configuration.TEST_TOKEN:
        TOKEN = configuration.TEST_TOKEN
    try:
        bot.run(TOKEN)
    except Exception as e:
        log.logger.warning(f"Not possible to start bot: Exception occurred {str(e)}")
