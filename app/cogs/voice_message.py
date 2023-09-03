import os
from time import time

import discord
import gtts
from discord import app_commands, errors
from discord.ext import commands

from app.cogs.translate import Translate
from app.configuration import MY_GUILD


class VoiceMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="v", description="Создать голосовое сообщение")
    @commands.cooldown(1, 17)
    @app_commands.guilds(MY_GUILD)
    async def v(self, ctx: commands.Context, *, text: str):
        try:
            await ctx.message.delete()
        except errors.NotFound:
            pass

        msg_language = Translate.determinate_language(text)
        audio_file = gtts.gTTS(text, lang=msg_language)
        file_name = str(time() * 10000) + ".mp3"
        audio_file.save(file_name)
        await ctx.send(
            f"Аудио сообщение от {ctx.message.author.name}",
            file=discord.File(file_name),
        )
        os.remove(file_name)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceMessage(bot), guild=MY_GUILD)
