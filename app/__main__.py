from app import TOKEN, log
from app.bot import bot

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        log.logger.warning(f"Not possible to start bot: Exception occurred {str(e)}")
