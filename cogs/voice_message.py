import os
from time import time

import discord
from discord.ext import commands
import gtts

from cogs.translate import Translate


class VoiceMessage(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def v(self, ctx, *, text: str):
        await ctx.message.delete()

        msg_language = Translate.determinate_language(text)
        audio_file = gtts.gTTS(text, lang=msg_language)
        file_name = str(time() * 10000) + ".mp3"
        audio_file.save(file_name)
        await ctx.send(
            f"Аудиосообщение от {ctx.message.author.name}",
            file=discord.File(file_name)
        )
        os.remove(file_name)
