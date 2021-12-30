import asyncio
from datetime import datetime, timedelta
from typing import Optional, NamedTuple
import re

import discord
from discord import User
from discord.channel import TextChannel
from discord.ext import commands
from discord.message import Message as DiscordMessage
from discord.ext.commands.cooldowns import BucketType
from discord.reaction import Reaction

from utils import fetch_all_channel_users
from configuration import VOTE_TIME


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
        "\N{REGIONAL INDICATOR SYMBOL LETTER Z}"
    ]

    def __init__(self, bot):
        self.bot = bot

    # parses the title, which should be in between curly brackets ('{title}')
    @staticmethod
    def find_title(message: str) -> Optional[str]:
        title = re.match("{(.+?)}", message)
        return title.group(1) if title else None

    # parses the options, which should be in between square brackets ('[option]')
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
            colour=0x83bae3,
        )
        embed_poll.set_footer(text=f"Голосование продлится {VOTE_TIME} минут")
        return embed_poll

    async def add_reaction(self, poll_message: DiscordMessage, options: list):
        emoji_letters_iterator = iter(self.emoji_letters)
        for _ in options:
            await poll_message.add_reaction(next(emoji_letters_iterator))

    @commands.cooldown(2, 60, BucketType.user)
    @commands.command(name="poll")
    async def poll(self, ctx, *, text: str):
        message = ctx.message

        title = self.find_title(text)
        if not title:
            await message.add_reaction('👍')
            await message.add_reaction('👎')
            await message.add_reaction('🤷')
            await message.channel.send(f"Голосование продлится {VOTE_TIME} минут")
            await self.add_for_tracking(message.id, message.channel, message.jump_url)

            return

        options = self.find_options(text)
        amount_of_options = len(options)
        if amount_of_options < 2:

            await message.channel.send(
                "Указана только одна опция пожалуйста используйте следующий формат:"
                "?poll: {Тема} [Вариант 1] [Вариант 2] [Вариант 3]"
            )
            return
        if amount_of_options > len(self.emoji_letters):
            await message.channel.send(
                f"Указана слишком много опций, пожалуйсте ограничтесь {len(self.emoji_letters)}"
            )
            return
        embed_poll = self.create_poll_message(options, title)
        poll_message = await message.channel.send(embed=embed_poll)
        await self.add_reaction(poll_message, options)
        await self.add_for_tracking(poll_message.id, message.channel, poll_message.jump_url, amount_of_options)

    @staticmethod
    async def add_for_tracking(message_id: int, channel: TextChannel, poll_message_url: str, amount_of_options: int):
        PollMessageTrack.poll_user_stats[message_id] = {}
        PollMessageTrack.amount_of_reactions[message_id] = amount_of_options
        await PollMessageTrack.run_vote_loop(message_id, channel, poll_message_url)


class UserReactions(NamedTuple):
    first_reaction: Reaction = None
    second_reaction: Optional[Reaction] = None


class PollMessageTrack:
    poll_user_stats: dict[int, dict[int, UserReactions]] = {}  # {message_id: {user_id: UserReactions}}
    amount_of_reactions: dict[int, int] = {}  # {message_id: amount_of_reactions}

    @classmethod
    async def run_vote_loop(cls, poll_message_id: int, channel: TextChannel, poll_message_url: str):
        amount_of_voters = len(fetch_all_channel_users(channel))
        time_tasks = 2
        current_moment = datetime.now()
        finish_poll_time = current_moment + timedelta(minutes=VOTE_TIME)
        first_time_task = current_moment + timedelta(minutes=VOTE_TIME//2)
        second_time_task = finish_poll_time - timedelta(minutes=5)

        while (current_moment := datetime.now()) < finish_poll_time:
            users_already_voted = len(cls.poll_user_stats[poll_message_id].keys())
            if users_already_voted >= amount_of_voters:
                break
            if current_moment > first_time_task and time_tasks == 2:
                time_tasks = 1
                description = f"До конца [голосования]({poll_message_url}) " \
                              f"осталось {VOTE_TIME//2} минут, " \
                              f"ваш мнение очеь важо для нас."
                await cls.send_poll_notification(description, channel)

            if current_moment > second_time_task and time_tasks == 1:
                time_tasks = 0
                description = f"До конца [голосования]({poll_message_url}) " \
                              f"остлось всего 5 минут," \
                              f" еще не поздно сделать вборсы."
                await cls.send_poll_notification(description, channel)
            await asyncio.sleep(15)
        await cls.send_results(poll_message_id, channel)

    @classmethod
    async def send_results(cls, message_id: int, channel: TextChannel):
        users_reaction_to_message = cls.poll_user_stats.pop(message_id)
        del cls.amount_of_reactions[message_id]
        reactions = [user_reaction.first_reaction for _, user_reaction in users_reaction_to_message.items()]
        message = await channel.fetch_message(message_id)

        if len(reactions) == len(set(reactions)) and len(reactions) < 2:
            description = f"[Голосование]({message.jump_url}) " \
                          f"завершилось победитель не выявлен"
            await cls.send_poll_notification(description, channel)
            return

        title, reaction_names = cls.fetch_message_info(message)
        emoji_top_reaction = str(max(reactions, key=reactions.count))
        if reaction_names:
            emoji_top_reaction = list(filter(lambda reaction: emoji_top_reaction in reaction, reaction_names))[0]

        description = f"**[Голосование]({message.jump_url}) завершилось.** " \
                      f"Больше всего голосов набрал вариант: \n\n {emoji_top_reaction}"
        await cls.send_poll_notification(description, channel, title=title)

    @classmethod
    async def save_or_update_reactions(cls, new_reaction: Reaction, user: User):
        message = new_reaction.message
        user_id = user.id
        users_reaction_to_message = cls.poll_user_stats[message.id]
        amount_of_reactions = cls.amount_of_reactions[message.id]
        allowed_reactions = Poll.emoji_letters[:amount_of_reactions]

        if new_reaction not in allowed_reactions:
            await new_reaction.remove(user)

        if user_id not in users_reaction_to_message:
            user_reaction = UserReactions(first_reaction=new_reaction)
            cls.poll_user_stats[message.id].update({user_id: user_reaction})
            return

        old_reaction = users_reaction_to_message[user_id].first_reaction
        await old_reaction.remove(user)
        # this will trigger on_raw_reaction_remove, and it will affect poll_user_stats,
        # that's why I need to keep two reactions
        new_users_reaction = {user_id: UserReactions(first_reaction=new_reaction, second_reaction=old_reaction)}
        cls.poll_user_stats[message.id].update(new_users_reaction)

    @classmethod
    async def process_removal_of_reaction(cls, message_id: int, user_id: int):
        users_reaction_to_message = cls.poll_user_stats[message_id]
        if user_id not in users_reaction_to_message:
            return

        user_previous_reactions = users_reaction_to_message.pop(user_id)
        if user_previous_reactions.second_reaction is not None:
            user_new_reactions = {user_id: UserReactions(
                first_reaction=user_previous_reactions.first_reaction,
                second_reaction=None)
            }
            cls.poll_user_stats[message_id].update(user_new_reactions)

    @classmethod
    def fetch_message_info(cls, message: DiscordMessage):
        if message.embeds:
            message_embed = message.embeds[0]
            title = message_embed.title
            reactions = message_embed.description.split("\n\n")
        else:
            message_intro = "?poll"
            title = message.content[len(message_intro):].strip()
            reactions = None
        return title, reactions

    @staticmethod
    async def send_poll_notification(string: str, channel: TextChannel, title=None):
        embed = discord.Embed(colour=0x83bae3)
        if title:
            embed.title = title
        embed.description = string
        await channel.send(embed=embed)
