from __future__ import annotations

import random
import re
import urllib.parse
from os import path

import aiohttp
import discord
import yaml
from bs4 import BeautifulSoup
from discord import Forbidden, app_commands, errors
from discord.ext import commands
from discord.ext.commands import CommandError
from loguru import logger

from app import NOTIFICATION_CHANNEL, TOKEN
from app.cogs.birthday_reminder import birthday_reminder
from app.cogs.poll import PollMessageTrack
from app.configuration import (
    MAIN_CHANNEL_ID,
    MAX_HIST_RETRIEVE_RECORDS,
    MY_GUILD,
    PREFIX,
    UMBRA_ID,
)
from app.utils import send_yaml_text, today
from app.utils.data.history_record import HistoryRecord
from app.utils.data.phrase import PhraseData
from app.utils.message_stats_routine import message_day_counter
from app.utils.webhooks import (
    fetch_web_hook_url,
    get_token_hash,
    set_web_hook_url,
    verify_url,
)
from app.utils.youtube_limiter import youtube_links_counter

HELLO_WORDS = ["ky", "ку"]
ANSWER_WORDS = ["помощь", "какая информация", "команды", "команды сервера", "что здесь делать"]
GOODBYE_WORDS = ["бб", "bb", "лан я пошел", "я спать"]


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents().all()
        super().__init__(command_prefix=PREFIX, intents=intents)
        self.poll_track = PollMessageTrack()  # poll_track used in cogs.message_stats
        self.caps = 0  # caps and nahooj variables changed in cogs.manage_users.ManageUser class
        self.nahooj = 0

    async def setup_hook(self) -> None:
        await self.load_extension("app.cogs.birthday_reminder")
        await self.load_extension("app.cogs.google_search")
        await self.load_extension("app.cogs.poll")
        await self.load_extension("app.cogs.translate")
        await self.load_extension("app.cogs.voice_message")
        await self.load_extension("app.cogs.message_stats")
        await self.load_extension("app.cogs.manage_users")
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self):
        birthday_reminder.set_bot(bot)

        message_day_counter.counter_routine.start()
        youtube_links_counter.set_limits_to_zero.start()
        await setup_web_hook()
        logger.info("Bot connected")

    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        await self.poll_track.save_or_update_reactions(reaction, user)

    async def on_raw_reaction_remove(self, payload):
        if payload.message_id not in self.poll_track.poll_message_data:
            return
        await self.poll_track.process_removal_of_reaction(payload.message_id, payload.user_id)

    async def on_command_error(self, ctx: commands.Context, exception: CommandError) -> None:
        try:
            await ctx.message.delete()
        except errors.NotFound:
            pass

        if isinstance(exception, discord.ext.commands.errors.CommandOnCooldown) or isinstance(
            exception,
            discord.app_commands.errors.CommandOnCooldown,
        ):
            await ctx.send(
                f"{ctx.message.author.name} погоди мой сладкий я почилю еще %.2f cек и тогда сделаю"
                f" все что смогу для тебя" % exception.retry_after,
            )
        elif isinstance(exception, discord.ext.commands.errors.CommandNotFound):
            await ctx.send(f"Команда {ctx.message.content} не была обнаружена")
        elif isinstance(exception, discord.ext.commands.errors.MissingRequiredArgument):
            await ctx.send(
                f"Команде {ctx.message.content} не хватает "
                f"аргументов, наберите ?cmds для подсказки",
            )
        else:
            logger.opt(exception=exception).error(f"Unexpected error {str(exception)} occurred.")

    async def on_message(self, message: discord.Message, /) -> None:
        message_day_counter.proceed_message_info(message)
        msg_text = message.content.lower()

        nahooj_message = self.parse_nahoj_message(message)
        if nahooj_message:
            await message.channel.send(nahooj_message)
            return

        await self.process_commands(message)

        if self.parse_youtube_link(message.content) and not youtube_links_counter.is_in_limit(
            message.author,
        ):
            await message.delete()
            await self.send_youtube_extend_links_message(message)
            return

        url_check = self.parse_url_link(message.content, message.author.id)
        if url_check:
            await message.delete()
            await message.channel.send(url_check)

        range_lox_word = self.parse_range_lox_word(msg_text)
        if range_lox_word:
            await message.delete()
            await message.channel.send(f"{message.author.name} слышь ч0рт, сам ты {range_lox_word}")
            return

        if (
            any(i.isalpha() for i in msg_text)
            and message.content.upper() == message.content
            and self.caps
        ):
            await message.delete()
            await message.channel.send(f"{message.author.name}: {message.content.capitalize()}")
        if msg_text in HELLO_WORDS:
            await message.channel.send("Привет, чо надо, идите нахуй я вас не знаю")
        elif msg_text in ANSWER_WORDS:
            await message.channel.send(f"напиши {PREFIX}cmds и тебе откроются все тайны")
        elif msg_text in GOODBYE_WORDS:
            await message.channel.send(f"{message.author.name} пиздуй бороздуй и я попиздил")
        elif "ливну" in msg_text:
            await message.channel.send(f"{message.author.name} давай уебывай уже отсюда")

    @staticmethod
    def parse_range_lox_word(msg_text: str) -> str | None:
        range_lox_regex = re.search(
            r"[\w\s]*[rр]+\s*[aа]+\s*[nн]+[\s*гrg]+\s*[aаeе]+[\s\w]*([лl]+\s*[0oо]+\s*(?:[hxхз]+|"
            r"(?:}{)+)|(?:]\[)+)[\w\s]*",
            msg_text,
        )
        if range_lox_regex:
            return range_lox_regex[1]

    @staticmethod
    def parse_url_link(msg_content: str, author_id: int) -> str | None:
        url_check = re.search(r"^(?:https?:\/\/)?(?:w{3}\.)?", msg_content.lower())
        if url_check and msg_content != urllib.parse.unquote(msg_content):
            message_content = urllib.parse.unquote(msg_content)
            return f"<@{author_id}>: {message_content}"

    @staticmethod
    def parse_youtube_link(msg_contnet: str) -> bool:
        youtube_check = re.match(
            r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch"
            r"\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?$",
            msg_contnet,
        )
        return bool(youtube_check)

    def parse_nahoj_message(self, message: discord.Message) -> str | None:
        if not UMBRA_ID:
            return

        msg_text = message.content.lower()
        nahoj_messages = [
            "Нахуй иди",
            "Съебался",
            f"Выполняю обработку команды {msg_text}, а нет не выполняю, иди нахуй, черт",
            "У меня перерыв 15 минут прошу простить",
            "Докажите что вы человек чтобы воспользоваться ботом",
            msg_text * 3,
        ]

        if self.nahooj and message.author.id == UMBRA_ID and message.channel.id == MAIN_CHANNEL_ID:
            if msg_text.startswith(PREFIX):
                return random.choice(nahoj_messages)

    @staticmethod
    async def send_youtube_extend_links_message(message: discord.Message):
        police_file_path = path.dirname(path.abspath(__file__)) + "/cat-wearing-police-suit.jpg"
        police_file = discord.File(police_file_path)

        await message.channel.send(
            f"Воу воу вы превышаете количество линков на YouTube в час гражданин. "
            f"Соблюдайте скоростной лимит, пожалуйста, "
            f"в {youtube_links_counter.max_youtube_limit} линк/час. "
            f"Счетчик обнулится примерно через {youtube_links_counter.get_time_to_reset()} минут.",
            file=police_file,
        )


bot = Bot()
bot.remove_command("help")


# add phrase
@bot.tree.command(name="dob", description="Добавить фразу в список", guild=MY_GUILD)
@app_commands.describe(
    author="Автор цитаты, опционально, если не указать будет использован автор сообщения.",
    text="Текст цитаты",
)
@app_commands.guilds(MY_GUILD)
async def dob(interaction: discord.Interaction, author: str | None = None, *, text: str):
    author = author or interaction.user.name
    PhraseData.insert(author=author, text=text)
    await interaction.response.send_message(f"Была добавлено фраза: {author}: {text}")


# get random phrase
@bot.hybrid_command(name="cit", description="Получить рандомную цитату", with_app_command=True)
@app_commands.guilds(MY_GUILD)
async def cit(ctx: commands.Context):
    data = PhraseData.get_random_phrase()
    if data is None:
        return await ctx.send(
            "Случайная фраза не была получена, воспользуйтесь"
            " сначала командой dob что бы добавить в базу",
        )
    author, text = data
    await ctx.send(f"{author}: {text}")


# add history log
@bot.tree.command(
    name="hist",
    description="Добавить запись с текстом text в историю",
    guild=MY_GUILD,
)
async def hist(interaction: discord.Interaction, *, text: str):
    HistoryRecord.insert(date=today(), log=text.capitalize())
    await interaction.response.send_message(
        f"{today().strftime('%d-%m-%Y')} - было добавлено воспоминание: {text}",
    )


@bot.hybrid_command(name="rec", description="Получить случайное воспоминание")
@app_commands.guilds(MY_GUILD)
@app_commands.describe(
    date="Дата когда искать. Формат дат: 30-05-2000; 05-2000; 2000",
    num=f"Номер записи с которой показать {MAX_HIST_RETRIEVE_RECORDS} записей. "
    f"Если 2 то со 2 по {MAX_HIST_RETRIEVE_RECORDS + 2}",
)
async def rec(ctx: commands.Context, date: str | None = None, num: int | None = None):
    result = HistoryRecord.get_record(date, offset=num)

    if type(result) is str:
        return await ctx.send(result)
    if not result:
        return await ctx.send(
            "Пожалуйста сначала добавьте воспоминания воспользовавшись командой hist",
        )
    output = ""
    for date, record in result:
        date_for_output = date.strftime("%d-%m-%Y")
        output += f"{date_for_output}: {record}\n"
    await ctx.send(output)


# clear
@bot.command(pass_contetx=True)
@commands.has_permissions(administrator=True)
async def clear(ctx: commands.Context, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)


@bot.hybrid_command(name="cmds", description="Список доступных команд")
@app_commands.guilds(MY_GUILD)
async def cmds(ctx: commands.Context):
    output = ""
    description_file_path = path.dirname(path.abspath(__file__)) + "/commands_description.yaml"

    await ctx.send("**Список доступных команд**")
    try:
        with open(description_file_path, encoding="utf-8") as file:
            commands_description = yaml.safe_load(file)["commands_description"]
    except FileNotFoundError:
        logger.opt(exception=True).error("Commands description with not found")
        await ctx.send(
            r"При попытки вызвать команду cmds произошла ошибка на стороне сервера, ¯\_(ツ)_/¯",
        )
        return
    for command_name, description in commands_description.items():
        prefix = PREFIX
        if command_name.startswith("/"):
            prefix = ""
        new_line = f"{prefix}{command_name}".ljust(20) + f"-- {description} \n"
        if len(output + new_line) > 2000:  # 2000 max message length
            await send_yaml_text(output, ctx)
            output = new_line
            continue
        output += new_line
    await send_yaml_text(output, ctx)

    languages_info = discord.Embed(
        title="Список языков и их сокращения",
        url="https://gist.githubusercontent.com/astronautlevel2/93a19379bd52b351dbc6eef269efa0bc/"
        "raw/18d55123bc85e2ef8f54e09007489ceff9b3ba51/langs.json",
    )
    await ctx.send(embed=languages_info)


@bot.hybrid_command(name="f", description="Получить случайный факт")
@app_commands.guilds(MY_GUILD)
async def f(ctx: commands.Context):
    member_name = ctx.author.name

    async with aiohttp.ClientSession() as session:
        site = "https://randstuff.ru/fact/"
        resp = await session.get(site)
        if resp.status != 200:
            logger.error(f"{resp.status} error while  sending a request to {site}")
            await ctx.send("Ошибка на стороне сервера повторите попытку позже")
            return
        text = await resp.text()

    soup = BeautifulSoup(text, "lxml")
    fact = soup.find("table", class_="text").find("td").text
    return await ctx.send(f"Интересный факт для {member_name}: \n{fact}")


@bot.hybrid_command(name="syll", description="Ограничение ссылок с YouTube (0 для отмены)")
@commands.has_permissions(administrator=True)
@app_commands.guilds(MY_GUILD)
async def set_youtube_link_limit(ctx: commands.Context, *, limit: int):
    if limit == 0:
        youtube_links_counter.set_youtube_link_limit(None)
        await ctx.send("Убран лимит на ссылки с youtube")
        return

    youtube_links_counter.set_youtube_link_limit(limit)
    await ctx.send(f"Лимит ссылок с ютуба в час равен {limit}")


async def setup_web_hook():
    if not NOTIFICATION_CHANNEL:
        logger.info("Webhook not set")
        return
    token_hash = get_token_hash(TOKEN)
    url = fetch_web_hook_url(token_hash)
    channel = bot.get_channel(NOTIFICATION_CHANNEL)
    if url and await verify_url(url, channel, bot):
        return

    try:
        webhook = await channel.create_webhook(name="Statistic")
    except Forbidden:
        logger.warning("Web Hook not created please provide this permission for the bot")
    else:
        set_web_hook_url(webhook.url, token_hash)
