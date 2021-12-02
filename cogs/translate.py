from typing import Optional

import discord
from discord.ext import commands
from googletrans import Translator, LANGUAGES
import langid

from configuration import DEFAULT_TRANSLATE_LANGUAGE


class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()

    @staticmethod
    def parse_user_desired_language(to_language: str) -> Optional[str]:
        to_language = to_language.lower()
        if to_language in ["rus", "ru"]:
            to_language = 'russian'
        elif to_language in ["eng", "en"]:
            to_language = 'english'
        elif to_language == 'ukr':
            to_language = 'ukrainian'
        else:
            to_language = LANGUAGES.get(to_language)

        return to_language

    @staticmethod
    def is_it_default_language(msg: str) -> bool:

        language = langid.classify(msg)[0]
        return LANGUAGES[language] == DEFAULT_TRANSLATE_LANGUAGE

    @staticmethod
    def create_output(translate: str, original_text: str, language: str) -> discord.Embed:
        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(name="Original", value=original_text, inline=False)
        embed.add_field(name=language, value=translate, inline=False)
        if translate == original_text:
            embed.add_field(name="Warning",
                            value="This language may not be supported by Google Translate."
                            )
        return embed

    @commands.command()
    async def trans(self, ctx, *, msg: str):
        """Translates words from one language to another. Do [p]cmds for more information.
        Usage:
        [p]trans [lang::] <words> - Translate words from one language to another.
        Short language name must be used.
        The original language will be assumed automatically.
        """
        to_language = None
        if msg.split()[0].endswith("::"):
            required_language = msg.split("::")[0]
            msg = msg[len(required_language) + 2:].strip()
            to_language = self.parse_user_desired_language(required_language)
            if to_language is None:
                await ctx.send(f"Указанный язык {required_language} не найден,"
                               f" использую {DEFAULT_TRANSLATE_LANGUAGE} в качестве языка для перевода.")
                to_language = DEFAULT_TRANSLATE_LANGUAGE

        if not to_language:
            if not self.is_it_default_language(msg):
                to_language = DEFAULT_TRANSLATE_LANGUAGE

        try:
            if to_language:
                result = self.translator.translate(msg, dest=to_language)
            else:
                result = self.translator.translate(msg)
        except Exception as e:
            print(e)
            await ctx.send("Произошла ошибка при переводе текста.")
            return

        translated_text, translated_language = result.text.capitalize(), LANGUAGES[result.dest]
        output_embed = self.create_output(translated_text, msg, translated_language)

        await ctx.send("", embed=output_embed)
