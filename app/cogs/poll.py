import asyncio
import re
from datetime import datetime, timedelta
from typing import NamedTuple, Optional

import discord
from discord import User, app_commands
from discord.channel import TextChannel
from discord.embeds import Embed
from discord.ext import commands
from discord.message import Message as DiscordMessage
from discord.reaction import Reaction

from app.configuration import MY_GUILD, VOTE_TIME
from app.utils import fetch_all_channel_users


class Poll(commands.Cog):
    emoji_letters = [
        "\N{REGIONAL INDICATOR SYMBOL LETTER A}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER B}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER C}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER D}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER E}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER F}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER G}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER H}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER I}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER J}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER K}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER L}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER M}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER N}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER O}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER P}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER Q}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER R}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER S}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER T}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER U}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER V}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER W}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER X}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER Y}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER Z}",
    ]

    emojis = ["👍", "👎", "🤷"]

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # parses the title, which should be in between curly brackets ("{title}")
    @staticmethod
    def find_title(message: str) -> str | None:
        title = re.match("{(.+?)}", message)
        return title.group(1) if title else None

    # parses the options, which should be in between square brackets ("[option]")
    @staticmethod
    def find_options(message: str) -> list[str]:
        options = re.findall(r"\[([^\[\]]+?)\]", message)
        return list(dict.fromkeys(options))

    def create_poll_message(self, options: list, title: str) -> discord.Embed:
        poll_message = ""
        for index, choice in enumerate(options):
            poll_message += "\n\n" + self.emoji_letters[index] + " " + choice
        embed_poll = discord.Embed(
            title="**" + title + "**",
            description=poll_message,
            colour=0x83BAE3,
        )
        embed_poll.set_footer(text=f"Голосование продлится {VOTE_TIME} минут")
        return embed_poll

    async def add_reaction(self, poll_message: DiscordMessage, options: list):
        emoji_letters_iterator = iter(self.emoji_letters)
        for _ in options:
            await poll_message.add_reaction(next(emoji_letters_iterator))

    @commands.command(name="poll", description="Начать голосование")
    @commands.cooldown(2, 60)
    @app_commands.guilds(MY_GUILD)
    @app_commands.describe(
        theme="Тема голосования",
        text=(
            "Варианты для голосования писать в "
            "квадратных скобках: [Вариант 1] [Вариант 2] [Вариант n]"
        ),
    )
    async def poll(self, ctx: commands.Context, theme: str, *, text: str):
        options = self.find_options(text)
        amount_of_options = len(options)
        if amount_of_options < 2:
            await ctx.send(
                "Указано недостаточной опций пожалуйста используйте следующий формат:"
                "[Вариант 1] [Вариант 2] [Вариант 3]",
            )
            return
        if amount_of_options > len(self.emoji_letters):
            await ctx.send(
                f"Указано слишком много опций, пожалуйсте ограничтесь {len(self.emoji_letters)}",
            )
            return
        embed_poll = self.create_poll_message(options, theme)
        poll_message = await ctx.send(embed=embed_poll)
        await self.add_reaction(poll_message, options)
        await self.add_for_tracking(poll_message, amount_of_options)

    async def add_for_tracking(self, message: DiscordMessage, amount_of_options: int):
        self.bot.poll_track.poll_user_stats[message.id] = {}
        self.bot.poll_track.amount_of_reactions[message.id] = amount_of_options
        await self.bot.poll_track.run_vote_loop(message.id, message.channel, message.jump_url)


class UserReactions(NamedTuple):
    first_reaction: Reaction = None
    second_reaction: Optional[Reaction] = None


class PollMessageTrack:
    def __init__(self):
        self.poll_user_stats: dict[DiscordMessage.id, dict[User.id, UserReactions]] = {}
        # {message_id: {user_id: UserReactions}}
        self.amount_of_reactions: dict[
            DiscordMessage.id,
            int,
        ] = {}  # {message_id:  amount_of_reactions}

    async def run_vote_loop(
        self,
        poll_message_id: int,
        channel: TextChannel,
        poll_message_url: str,
    ):
        amount_of_voters = len(fetch_all_channel_users(channel)) - 1  # -1 only for my chanel :D
        time_tasks = 2  # scheduled reminders
        current_moment = datetime.now()
        finish_poll_time = current_moment + timedelta(minutes=VOTE_TIME)
        first_time_task = current_moment + timedelta(minutes=VOTE_TIME // 2)
        second_time_task = finish_poll_time - timedelta(minutes=5)

        message = await channel.fetch_message(poll_message_id)
        title, _, _ = self.fetch_message_info(message)

        while (current_moment := datetime.now()) < finish_poll_time:
            users_already_voted = len(self.poll_user_stats[poll_message_id].keys())
            if users_already_voted >= amount_of_voters:
                break

            if current_moment > first_time_task and time_tasks == 2:
                time_tasks = 1
                description = (
                    f"До конца [голосования]({poll_message_url}) "
                    f"осталось {VOTE_TIME//2} минут, "
                    f"ваш мнение очень важно для нас."
                )
                await self.send_poll_notification(description, channel, title=title)

            if current_moment > second_time_task and time_tasks == 1:
                time_tasks = 0
                description = (
                    f"До конца [голосования]({poll_message_url}) "
                    f"остлось всего 5 минут,"
                    f" еще не поздно сделать вбросы."
                )
                await self.send_poll_notification(description, channel, title=title)
            await asyncio.sleep(15)
        await self.send_results(message, channel)

    async def send_results(self, message: DiscordMessage, channel: TextChannel):
        title, reaction_names, message_id = self.fetch_message_info(message)

        users_reaction_to_message = self.poll_user_stats.pop(message_id)
        del self.amount_of_reactions[message_id]
        reactions = [
            user_reaction.first_reaction for _, user_reaction in users_reaction_to_message.items()
        ]

        if len(reactions) == len(set(reactions)) and len(reactions) != 1:
            description = f"[Голосование]({message.jump_url}) " f"завершилось победитель не выявлен"
            await self.send_poll_notification(description, channel, title=title)
            return

        emoji_top_reaction = str(max(reactions, key=reactions.count))
        if reaction_names:
            emoji_top_reaction = list(
                filter(lambda reaction: emoji_top_reaction in reaction, reaction_names),
            )[0]

        description = (
            f"**[Голосование]({message.jump_url}) завершилось.** "
            f"Больше всего голосов набрал вариант: \n\n {emoji_top_reaction}"
        )
        result_message = await self.send_poll_notification(description, channel, title=title)
        await self.mark_finished(message, result_message)

    async def save_or_update_reactions(self, new_reaction: Reaction, user: User):
        if new_reaction.message.id not in self.poll_user_stats:
            return

        message = new_reaction.message
        user_id = user.id
        users_reaction_to_message = self.poll_user_stats[message.id]
        allowed_reactions = self.parse_allowed_reactions(message)

        if str(new_reaction) not in allowed_reactions:
            await new_reaction.remove(user)
            return

        if user_id not in users_reaction_to_message:
            user_reaction = UserReactions(first_reaction=new_reaction)
            self.poll_user_stats[message.id].update({user_id: user_reaction})
            return

        old_reaction = users_reaction_to_message[user_id].first_reaction
        await old_reaction.remove(user)
        # this will trigger on_raw_reaction_remove, and it will affect poll_user_stats,
        # that"s why I need to keep two reactions
        new_users_reaction = {
            user_id: UserReactions(first_reaction=new_reaction, second_reaction=old_reaction),
        }
        self.poll_user_stats[message.id].update(new_users_reaction)

    async def process_removal_of_reaction(self, message_id: int, user_id: int):
        users_reaction_to_message = self.poll_user_stats[message_id]
        if user_id not in users_reaction_to_message:
            return

        user_previous_reactions = users_reaction_to_message[user_id]
        if user_previous_reactions.second_reaction is not None:
            user_new_reactions = {
                user_id: UserReactions(
                    first_reaction=user_previous_reactions.first_reaction,
                    second_reaction=None,
                ),
            }
            self.poll_user_stats[message_id].update(user_new_reactions)

    @staticmethod
    def fetch_message_info(message: DiscordMessage) -> tuple[str, str, int]:
        if message.embeds:
            message_embed = message.embeds[0]
            title = message_embed.title
            reactions = message_embed.description.split("\n\n")
        else:
            message_intro = "?poll"
            title = message.content[len(message_intro) :].strip()  # noqa E203
            reactions = None
        return title, reactions, message.id

    @staticmethod
    async def send_poll_notification(
        string: str,
        channel: TextChannel,
        title=None,
    ) -> DiscordMessage:
        embed = discord.Embed(colour=0x83BAE3)
        if title:
            embed.title = title
        embed.description = string
        result_message = await channel.send(embed=embed)
        return result_message

    def parse_allowed_reactions(self, message: DiscordMessage) -> list:
        if not message.embeds:
            return Poll.emojis
        amount_of_reactions = self.amount_of_reactions[message.id]
        allowed_reactions = Poll.emoji_letters[:amount_of_reactions]
        return allowed_reactions

    @staticmethod
    async def mark_finished(poll_message: DiscordMessage, result_message: discord.Message):
        if poll_message.embeds:
            message_embed = poll_message.embeds[0]
            description = message_embed.description
            description += f"\n\nГолсование окончено. Результаты [тут]({result_message.jump_url})."
            new_embed = Embed(title=message_embed.title, description=description)
            await poll_message.edit(embed=new_embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Poll(bot), guild=MY_GUILD)
