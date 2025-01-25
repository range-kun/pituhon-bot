from app import TOKEN, log
from app.bot import discord_bot

if __name__ == "__main__":
    try:
        discord_bot.run(TOKEN)
    except Exception as e:
        log.logger.warning(f"Not possible to start bot: Exception occurred {str(e)}")
