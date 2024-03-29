from __future__ import annotations

from datetime import date

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext.commands.bot import Bot as DiscordBot
from tabulate import tabulate

from app.configuration import MY_GUILD
from app.utils.data import Data
from app.utils.data.channel_stats import ServerStats
from app.utils.data.user_stats import UserCurrentStats, UserMaxStats, UserOverallStats
from app.utils.message_stats_routine import message_day_counter


class MessageStats(commands.Cog):
    def __init__(self, bot: DiscordBot):
        self.bot = bot

    @commands.hybrid_command(description="Получить статистику сообщений", name="stats")
    @app_commands.choices(
        option=[
            app_commands.Choice(name="Статистика за день", value="day"),
            app_commands.Choice(name="Статистика рекордов", value="champ"),
            app_commands.Choice(name="Статистика сервера", value="ch"),
        ],
    )
    @app_commands.guilds(MY_GUILD)
    async def stats(self, ctx: commands.Context, *, option: Choice[str] | None = None):
        if not option:
            await self.proceed_users_data(ctx, ctx.author)
            return

        text = option.value
        if text == "day":
            await self.proceed_users_day_data(ctx, ctx.author)
        elif text == "ch":
            await self.proceed_channel_stats(ctx, ctx.author)
        elif text == "champ":
            await self.proceed_champ_stats(ctx, ctx.author)
        else:
            await ctx.send(
                f"Бот не может обработать статистику {text}, "
                f"воспользуйтесь ?cmd для просмотра опций",
            )

    async def proceed_users_data(self, ctx: commands.Context, author: discord.User):
        users_current_info, user_max_info = self.collect_users_info(author.id)

        current_structure = MessageStructure.create_user_current_structure(
            users_current_info,
            author.id,
        )
        max_structure = MessageStructure.create_user_max_structure(user_max_info)

        if not max_structure and not current_structure:
            await ctx.send(f"Статистика по запросу {author.name} в базе не найдена")

        if current_structure:
            current_structure = str(f"```yaml\n{current_structure}```")
        if max_structure:
            max_structure = str(f"```yaml\n{max_structure}```")

        data_dict = {"Текущая статистика": current_structure, "Рекордная статистика": max_structure}
        info = self.create_output_embed(
            author,
            data_dict,
            title=f"Статистика сообщений {author.name}",
        )
        await ctx.send(embed=info)

    async def proceed_users_day_data(self, ctx: commands.Context, author: discord.User):
        author_stats = message_day_counter.authors.get(author.id)
        if not author_stats:
            await ctx.send("Напишите еще что нибудь")
            return

        user_data = MessageStructure.create_author_day_data(
            author_stats.amount_of_messages,
            author_stats.amount_of_symbols,
        )
        info = self.create_output_embed(
            author,
            user_data,
            title=f"Статистика сообщений {author.name}",
        )
        await ctx.send(embed=info)

    async def proceed_channel_stats(self, ctx: commands.Context, author: discord.User):
        with ServerStats.begin() as connection:
            max_message_data, max_symbols_data = ServerStats.fetch_all_data(connection)
            messages, symbols = UserOverallStats.fetch_overall_data(connection)

        if not max_message_data and not messages:
            await ctx.send("Статистика сервера пока не найдена, обратитесь позже.")
            return

        max_stats_structure = MessageStructure.create_server_max_structure(
            max_message_data,
            max_symbols_data,
        )
        max_stats_structure = str(f"```yaml\n{max_stats_structure}```")

        overall_stats_structure = MessageStructure.create_server_overall_structure(
            (messages, symbols),
            (message_day_counter.messages, message_day_counter.symbols),
        )
        overall_stats_structure = str(f"```yaml\n{overall_stats_structure}```")

        data_dict = {
            "Рекордная статистика": max_stats_structure,
            "Суммарные данные": overall_stats_structure,
        }
        info = self.create_output_embed(author, data_dict, title="Статистика сервера")
        await ctx.send(embed=info)

    async def proceed_champ_stats(self, ctx: commands.Context, author: discord.User):
        champ_stats = UserMaxStats.fetch_champions_stats()
        champs_structure = await MessageStructure.create_champs_structure(self.bot, champ_stats)

        if not champs_structure:
            await ctx.send("Статистика рекордсменов в базе не найдена")
            return

        champs_structure = str(f"```yaml\n{champs_structure}```")
        data_dict = {"====================": champs_structure}
        info = self.create_output_embed(author, data_dict, title="Статистика рекордов")
        await ctx.send(embed=info)

    @staticmethod
    def collect_users_info(user_id: int):
        with Data.do_with_session() as session:
            user_current_info = UserCurrentStats.fetch_single_user_db_stats(session, user_id)
            user_max_info = UserMaxStats.fetch_user_db_max_stats(session, user_id)
        return user_current_info, user_max_info

    @staticmethod
    def create_output_embed(
        author: discord.User,
        data_dict: dict[str, str],
        *,
        title: str,
    ) -> discord.Embed:
        info = discord.Embed(title=title, color=discord.Color.green())
        info.set_author(name=author.name, icon_url=author.display_avatar)
        for name, value in data_dict.items():
            info.add_field(name=name, value=value or "Информации пока нет")

        return info


class MessageStructure:
    @classmethod
    def create_user_current_structure(cls, user_current_info: list, user_id: id) -> str | None:
        current_stats_structure = [
            ["Кол-во \nсообщений", "Кол-во \nсимволов"],
        ]
        author_stats = message_day_counter.authors.get(user_id)
        if not author_stats and not user_current_info:
            return

        if user_current_info:
            period_info = [["Всё", "время"], ["Текущий", "месяц"], ["Текущая", "неделя"]]

            for period, messages, symbols in zip(
                period_info,
                user_current_info[0::2],
                user_current_info[1::2],
            ):
                current_stats_structure.append(period)
                current_stats_structure.append([messages, symbols])
        if author_stats:
            current_stats_structure.append(["Текущий", "день"])
            current_stats_structure.append(
                [author_stats.amount_of_messages, author_stats.amount_of_symbols],
            )

        return tabulate(current_stats_structure, headers="firstrow", tablefmt="pretty")

    @classmethod
    def create_user_max_structure(cls, user_max_info: list[date, int]) -> str | None:
        max_stats_structure = [
            ["Кол-во", "Дата \nфиксации"],
        ]
        headers = [
            ["Сообщений", "за день"],
            ["Символов", "за день"],
            ["Сообщений", "за неделю"],
            ["Символов", "за неделю"],
            ["Сообщений", "за месяц"],
            ["Символов", "за месяц"],
        ]
        for period, amount, record_date in zip(headers, user_max_info[0::2], user_max_info[1::2]):
            if not amount:
                continue
            record_date = cls.format_record_date(
                is_month=period[1] == "за месяц",
                record_date=record_date,
            )

            max_stats_structure.append(period)
            max_stats_structure.append([amount, record_date])
        if len(max_stats_structure) == 1:
            return

        return tabulate(max_stats_structure, headers="firstrow", tablefmt="rst")

    @classmethod
    def create_server_max_structure(
        cls,
        message_stats: list[tuple],
        symbol_stats: list[tuple],
    ) -> str:
        max_stats_structure = [
            ["Кол-во", "Дата \nфиксации"],
        ]
        symbols_headers = {
            "day": ["Символов", "за день"],
            "week": ["Символов", "за неделю"],
            "month": ["Символов", "за месяц"],
        }
        message_headers = {
            "day": ["Сообщений", "за день"],
            "week": ["Сообщений", "за неделю"],
            "month": ["Сообщений", "за месяц"],
        }

        for headers, stats_collection in zip(
            [message_headers, symbols_headers],
            [message_stats, symbol_stats],
        ):
            for period in headers:  # to order from days to month
                channel_stats = filter(
                    lambda period_info: period in list(period_info),
                    stats_collection,
                )

                try:
                    _, record_date, amount = list(channel_stats)[0]
                except ValueError:
                    return "Статистика рекордов не была обнаружена, попробуйте позже."

                record_date = cls.format_record_date(
                    is_month=period == "month",
                    record_date=record_date,
                )

                max_stats_structure.append(headers[period])
                max_stats_structure.append([amount, record_date])
        return tabulate(max_stats_structure, headers="firstrow", tablefmt="rst")

    @classmethod
    def create_author_day_data(cls, messages: int, symbols: int) -> dict[str, str]:
        day_info = f"Кол-во сообщений  =>{messages}\n" f"Кол-во символов  =>{symbols}"
        return {"За сегодня:": day_info}

    @classmethod
    def create_server_overall_structure(
        cls,
        overall_stats: tuple[int, int],
        today_stats: tuple[int, int],
    ) -> str | None:
        db_messages, db_symbols = overall_stats
        today_messages, today_symbols = today_stats
        overall_messages = db_messages + today_messages
        overall_symbols = db_symbols + today_symbols

        overall_stats_structure = [
            ["Кол-во \nсообщений", "Кол-во \nсимволов"],
            ["Статистика", "за сегодня"],
            [today_messages, today_symbols],
            ["Суммарная", "статистика"],
            [overall_messages, overall_symbols],
        ]
        return tabulate(overall_stats_structure, headers="firstrow", tablefmt="rst")

    @classmethod
    async def create_champs_structure(
        cls,
        bot: DiscordBot,
        champ_stats: list[tuple[int, int]],
    ) -> str | None:
        champs_structure = [
            ["Рекордсмен", "Кол-во"],
        ]
        headers = [
            ["Сообщений", "за день"],
            ["Символов", "за день"],
            ["Сообщений", "за неделю"],
            ["Символов", "за неделю"],
            ["Сообщений", "за месяц"],
            ["Символов", "за месяц"],
        ]

        for period, champ_user_info in zip(headers, champ_stats):
            if not champ_user_info:
                continue
            user_id, amount = champ_user_info
            user = await bot.fetch_user(user_id)
            champs_structure.append(period)
            champs_structure.append([user.name, amount])
        if len(champs_structure) == 1:
            return

        return tabulate(champs_structure, headers="firstrow", tablefmt="fancy_grid")

    @classmethod
    def format_record_date(cls, *, is_month: bool, record_date: date) -> str:
        if is_month:
            record_date = record_date.strftime("%m-%Y")
        else:
            record_date = record_date.strftime("%d-%m-%Y")

        return record_date


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageStats(bot), guild=MY_GUILD)
