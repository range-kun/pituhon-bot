from __future__ import annotations

import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from app.configuration import MY_GUILD

# mute


class ManageUsers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_contetx=True)
    @commands.has_permissions(administrator=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: int = 1):
        mute_role = discord.utils.get(ctx.message.guild.roles, name="mute")
        if mute_role in member.roles:
            await ctx.send(f"{member} уже замучен")
            return

        tail = (
            f"{duration} час"
            + "a" * (1 < duration % 10 < 5 and duration not in range(5, 21))
            + "ов" * (4 < duration % 10 < 9 or duration in range(5, 21) or duration % 10 == 0)
        )

        await member.add_roles(mute_role)
        overwrite = discord.PermissionOverwrite(send_messages=False)
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(mute_role, overwrite=overwrite)
        await ctx.send(f"{member.mention} был замьючен на {tail}")
        await asyncio.sleep(duration * 3600)
        await member.remove_roles(mute_role)

    @commands.command(pass_contetx=True)
    @commands.has_permissions(administrator=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        mute_role = discord.utils.get(ctx.message.guild.roles, name="mute")
        if mute_role not in member.roles:
            await ctx.send(f"{member} не замучен")
            return
        else:
            await member.remove_roles(mute_role)
            await ctx.send(f"{member.mention} отмьючен")
            return

    @commands.command(pass_contetx=True)
    @commands.has_permissions(administrator=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str | None = None,
    ):
        await ctx.message.delete()
        await member.kick(reason=reason)
        await ctx.send(f"Выгнали {member.mention} на мороз")

    @commands.command(pass_contetx=True)
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        await ctx.message.delete()
        try:
            await member.ban(reason=reason)
        except commands.errors.MemberNotFound:
            await ctx.send(f"Участник {member.mention} не найден")
        await ctx.send(f"Такие как {member.mention} нам явно не нужны")

    @commands.command(pass_contetx=True)
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx: commands.Context, *, member: str):
        banned_users = [entry async for entry in ctx.guild.bans(limit=2000)]
        info = [(ban_entry.user.name, ban_entry.user.discriminator) for ban_entry in banned_users]

        try:
            member_name, member_discriminator = member.split("#")
        except ValueError:
            await ctx.send(
                "Введены неверные данные пользователя, пожалуйста воспользуйтесь "
                "следующим форматом: username#id -> test_lexa#9087",
            )
            return

        if (member_name, member_discriminator) in info:
            for ban_entry in banned_users:
                user = ban_entry.user
                if (user.name, user.discriminator) == (member_name, member_discriminator):
                    await ctx.guild.unban(user)
                    await ctx.send(f"Разбанен {user}")
                    return
        else:
            await ctx.send(f"Пользователь {member} не найден в списке забаненных")

    @commands.hybrid_command(
        name="ban_list",
        description="Показать список забаненных пользователей",
    )
    @app_commands.guilds(MY_GUILD)
    async def show_ban_list(self, ctx: commands.Context):
        ban_list = [entry async for entry in ctx.guild.bans(limit=2000)]
        if not ban_list:
            await ctx.send("В данный момент нету заблокированных пользователей")
            return

        info = discord.Embed(title="Список забаненных пользователей", color=discord.Color.green())
        info.add_field(name="Пользователь", value="Причина")
        for entry in ban_list:
            info.add_field(name=entry.user, value=entry.reason)
        await ctx.send(embed=info)

    # forbid to use CAPSLOCK
    @commands.command(pass_contetx=True)
    @commands.has_permissions(administrator=True)
    async def caps(self, ctx: commands.Context):
        self.bot.caps = 0 if self.bot.caps else 1
        caps_info = {0: "Caps allowed", 1: "Caps not allowed"}
        await ctx.send(caps_info[self.bot.caps])

    @commands.command(pass_contetx=True)
    @commands.has_permissions(administrator=True)
    async def nah(self, ctx: commands.Context):
        self.bot.nahooj = 0 if self.bot.nahooj else 1
        nahhoj_info = {0: "Ne nahooj", 1: "Nahooy"}
        await ctx.send(nahhoj_info[self.bot.nahooj])


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ManageUsers(bot), guild=MY_GUILD)
