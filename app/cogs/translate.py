from __future__ import annotations

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from googletrans import LANGUAGES, Translator

from app.configuration import MY_GUILD
from app.constants import DEFAULT_TRANSLATE_LANGUAGE
from app.log import logger

LANGUAGES_NAMES = {
    "Английский": "en",
    "Арабский": "ar",
    "Вьетнамский": "vi",
    "Голландский": "nl",
    "Греческий": "el",
    "Индонезийский": "id",
    "Итальянский": "it",
    "Казахский": "kk",
    "Китайский": "zh-cn",
    "Корейский": "ko",
    "Латинский": "la",
    "Немецкий": "de",
    "Персидский": "fa",
    "Польский": "pl",
    "Португальский": "pt",
    "Русский": "ru",
    "Суахили": "sw",
    "Тай": "th",
    "Турецкий": "tr",
    "Украинский": "uk",
    "Финский": "fi",
    "Французский": "fr",
    "Хинду": "hi",
    "Чешский": "cs",
    "Японский": "ja",
}
CHOICES = [app_commands.Choice(name=key, value=value) for key, value in LANGUAGES_NAMES.items()]


class Translate(commands.Cog):
    translator = Translator()

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @classmethod
    def determinate_language(cls, msg: str) -> str:
        return cls.translator.detect(msg).lang

    @staticmethod
    def parse_user_desired_language(autocomplete_lang: Choice, extra_lang: str) -> str | None:
        if autocomplete_lang:
            return autocomplete_lang.value
        if not extra_lang:
            return None

        to_language = extra_lang.lower()
        if to_language in ["rus", "ru"]:
            to_language = "russian"
        elif to_language in ["eng", "en"]:
            to_language = "english"
        elif to_language == "ukr":
            to_language = "ukrainian"
        else:
            to_language = LANGUAGES.get(to_language)

        return to_language

    @staticmethod
    def create_output(
        translate: str,
        original_text: str,
        language: str,
        original_language: str,
    ) -> discord.Embed:
        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(name=f"Original -> {original_language}", value=original_text, inline=False)
        embed.add_field(name=language, value=translate, inline=False)
        if translate == original_text:
            embed.add_field(
                name="Warning",
                value="This language may not be supported by Google Translate.",
            )
        return embed

    @app_commands.command(
        name="trans",
        description="Перевести фразу, по-умолчанию русско - английская пара.",
    )
    @app_commands.guilds(MY_GUILD)
    @app_commands.describe(
        autocomplete_lang="Самые популярные языки, на которые необходимо перевести",
        any_lang=(
            "Вручную ввести язык перевода, если нету нужного"
            " в autocomplete_lang (названия смотреть в /cmds)"
        ),
        text="Текст для перевода.",
    )
    @app_commands.choices(autocomplete_lang=CHOICES)
    async def trans(
        self,
        interaction: discord.Interaction,
        autocomplete_lang: Choice[str] | None = None,
        any_lang: str | None = None,
        *,
        text: str,
    ):
        if any_lang and autocomplete_lang:
            await interaction.response.send_message(
                "Указано одновременно два параметра autocomplete_lang и extra_lang, "
                "пожалуйста выберите только один параметр.",
            )
            return

        message_language = LANGUAGES.get(self.determinate_language(text))
        to_language = self.parse_user_desired_language(autocomplete_lang, any_lang)

        if to_language is None and any_lang:
            language_response = [DEFAULT_TRANSLATE_LANGUAGE, "english"][
                message_language == DEFAULT_TRANSLATE_LANGUAGE
            ]
            await interaction.channel.send(
                f"Указанный язык {any_lang} не найден, "
                f"использую {language_response} в качестве языка для перевода.",
            )

        if not to_language and not message_language == DEFAULT_TRANSLATE_LANGUAGE:
            to_language = DEFAULT_TRANSLATE_LANGUAGE

        try:
            if to_language:
                result = self.translator.translate(text, dest=to_language)
            else:
                result = self.translator.translate(text)
        except Exception as e:
            logger.opt(exception=True).error(
                f"Exception occurred {str(e)} while "
                f"translating: \n {text} to {to_language or 'english'}",
            )
            await interaction.channel.send("Произошла ошибка при переводе текста.")
            return

        translated_text, translated_language = result.text.capitalize(), LANGUAGES[result.dest]
        output_embed = self.create_output(
            translated_text,
            text,
            translated_language,
            message_language,
        )

        await interaction.response.send_message(embed=output_embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Translate(bot), guild=MY_GUILD)
