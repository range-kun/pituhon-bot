import os
from time import time

import discord
from discord.ext import commands
import gtts
import langid


class VoiceMessage(commands.Cog):

    @commands.command()
    async def v(self, ctx, *, text: str):
        await ctx.message.delete()
        message_language = langid.classify(text)[0]
        t1 = gtts.gTTS(text, lang=message_language)
        file_name = str(time() * 10000) + ".mp3"
        t1.save(file_name)
        await ctx.send(text, "Language", message_language)
        await ctx.send(
            f"Аудиосообщение от {ctx.message.author.name}",
            file=discord.File(file_name)
        )
        os.remove(file_name)
