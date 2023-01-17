from datetime import datetime, time

import discord
from discord import ButtonStyle, Embed, ui, Interaction
from discord import app_commands, User
from discord.ext import commands, tasks
from sqlalchemy.engine import Row

from app import NOTIFICATION_CHANNEL
from app.configuration import MY_GUILD
from app.log import logger
from app.utils import tomorrow_text_type, BotSetter, catch_exception
from app.utils.data.birthday_reminder import BirthdayDataReminder


class BirthdayCRUD(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="bl", description="Показать список именниников :)")
    @app_commands.guilds(MY_GUILD)
    async def birthday_list(self, ctx: commands.Context):
        birthday_users = BirthdayDataReminder.get_all_birthday_users()

        if not birthday_users:
            await ctx.send("Нету пользователей в базе, для добавление воспользуйтесь командой /ba")
            return
        user_embed = await self.create_birthday_list_embed(birthday_users)
        await ctx.send(embed=user_embed)

    async def create_birthday_list_embed(self, birthday_users: list[Row]) -> Embed:
        user_embed = Embed(title="Список пользователей и их дни рождения")
        for user_id, birth_date in birthday_users:
            user = await self.bot.fetch_user(user_id)
            user_embed.add_field(
                name=f"{user.name} id-> {user_id}",
                value=birth_date.strftime("%Y-%m-%d"),
                inline=False
            )
        return user_embed

    @commands.hybrid_command(name="bd", description="Удалить пользователя из базы именниников")
    @commands.has_permissions(administrator=True)
    @app_commands.guilds(MY_GUILD)
    @app_commands.describe(
        user_id="Id нужного пользователя (ПКМ -> упомняуть)",
    )
    async def delete_birthday(self, ctx: commands.Context, user_id: str):
        try:
            user_id = int(user_id)
        except ValueError:
            await ctx.send("Указан неверный формат id пользователя")
            return

        if BirthdayDataReminder.is_user_in_db(user_id):
            await self.confirm_delete(user_id, ctx)
        else:
            await ctx.send(
                "Пользователь с данным id отстуствует в базе именниников."
                " Посмотреть список можно воспользовавшись командой /bl"
            )

    async def confirm_delete(self, user_id: int, ctx: commands.Context):
        response_view = self.create_response_for_delete_birthday(user_id)
        await ctx.send("Удалить пользователя из базы именниников?", view=await response_view)

    async def create_response_for_delete_birthday(self, user_id: int) -> ui.View:
        view = ui.View()

        green_button = ui.Button(style=ButtonStyle.green, label="Оставить")
        green_button.callback = lambda interaction: self.dont_delete_callback(interaction, user_id)

        red_button = ui.Button(style=ButtonStyle.red, label="Удалить")
        red_button.callback = lambda interaction: self.delete_birthday_callback(interaction, user_id)

        view.add_item(item=green_button)
        view.add_item(item=red_button)
        return view

    @staticmethod
    async def delete_birthday_callback(interaction: Interaction, user_id: int):
        BirthdayDataReminder.delete(
            condition=(BirthdayDataReminder.get_table().c.user_id == user_id)
        )
        await interaction.response.send_message(f"День рождение <@{user_id}> удален из базы.")

    @staticmethod
    async def dont_delete_callback(interaction: Interaction, user_id: int):
        await interaction.response.send_message(f"День рождение <@{user_id}> остался в базе.")

    @commands.hybrid_command(name="ba", description="Добавить нового иммениника в базу")
    @commands.has_permissions(administrator=True)
    @app_commands.guilds(MY_GUILD)
    @app_commands.describe(
        user="Нужный пользователь (ПКМ -> упомняуть)",
        input_birth_date="День рождения в формате ГГГГ-мм-дд: 1952-10-07",
    )
    async def add_birthday(self, ctx: commands.Context, user: User, input_birth_date: str):
        if not self.is_valid_date(input_birth_date):
            await ctx.send(f"Указан некоректный формат даты {input_birth_date}: ГГГГ-мм-дд: 1952-10-07")
            return

        birthday_in_db_date = BirthdayDataReminder.get_user_birth_day(user.id)
        if birthday_in_db_date:
            await self.update_birthday(ctx, user, birthday_in_db_date, input_birth_date)
            return

        BirthdayDataReminder.insert(date=input_birth_date, user_id=user.id)
        await ctx.send(
            f"День рождение {input_birth_date} пользователя {user.name} было добавлено в базу."
        )

    @staticmethod
    def is_valid_date(date: str) -> bool:
        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return False
        if datetime.now() < date:
            return False
        return True

    async def update_birthday(self, ctx: commands.Context, user: User, date_in_db: str, new_date: str):
        response_view = self.create_response_for_new_birthday(user.id, new_date)
        info = Embed(
            title=f"День рождение {user.name} уже добавлено в базу",
            color=discord.Color.green()
        )
        info.add_field(
            name=f"Пользователь уже имеется в базе с днем рождения {date_in_db}",
            value=f"Обновить данное значение на **{new_date}** ?")
        await ctx.send(embed=info, view=await response_view)

    async def create_response_for_new_birthday(self, user_id: int, birth_date: str) -> ui.View:
        view = ui.View()

        green_button = ui.Button(style=ButtonStyle.green, label="Обновить")
        green_button.callback = lambda interaction: self.renew_button_callback(interaction, user_id, birth_date)

        red_button = ui.Button(style=ButtonStyle.red, label="Не обновлять")
        red_button.callback = lambda interaction: self.dont_update_callback(interaction, user_id)

        view.add_item(item=green_button)
        view.add_item(item=red_button)
        return view

    @staticmethod
    async def renew_button_callback(interaction: Interaction, user_id: int, birth_date: str):
        BirthdayDataReminder.update(
            date=birth_date,
            condition=(BirthdayDataReminder.get_table().c.user_id == user_id)
        )
        await interaction.response.send_message(
            f"Установлено новое значение {birth_date} дня рождения, для пользователя <@{user_id}>"
        )

    @staticmethod
    async def dont_update_callback(interaction: Interaction, user_id: int):
        await interaction.response.send_message(f"День рождение <@{user_id}> остался прежним.")


class BirthdayReminder(BotSetter):
    tz = datetime.now().astimezone().tzinfo
    daily_time = time(hour=23, minute=25, tzinfo=tz)

    @tasks.loop(time=daily_time)
    @catch_exception
    async def remind_birthday_routine(self):
        birthday_data_query = BirthdayDataReminder.get_birthdays_for_next_day()
        if birthday_data_query is None:
            return

        birthday_data_list = [user_id[0] for user_id in birthday_data_query]
        birthday_users = await self.get_users(birthday_data_list)
        await self.send_reminds(birthday_users)
        logger.info("Successfully send reminds for tomorrow")

    async def get_users(self, birthday_data_list: list[int]) -> list[User]:
        return [await self.bot.fetch_user(user_id) for user_id in birthday_data_list]

    async def send_reminds(self, birthday_users: list[User]):
        if NOTIFICATION_CHANNEL is None:
            return
        channel = self.bot.get_channel(NOTIFICATION_CHANNEL)
        users = ", ".join(f"<@{user.id}>" for user in birthday_users)
        if len(birthday_users) > 1:
            await channel.send(
                f"{tomorrow_text_type()} у {users} день рождения 🎂, давайте мы их дружно поздравим."
            )
        else:
            await channel.send(
                f"{tomorrow_text_type()} у {users} день рождение, похлопаем нашему имениннику 🥳."
            )


birthday_reminder = BirthdayReminder()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BirthdayCRUD(bot), guild=MY_GUILD)
