import discord
from discord.ext import commands


class ChanelStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_data_for_day(channel, authors, messages, symbols, client):
        emb = discord.Embed(title='Информация по серверу за 24 часа', colour=discord.Color.dark_blue())
        temp_list_messages = sorted(list(authors.items()),
                                    key=lambda i: i[1][0], reverse=True)[0]
        temp_list_symbols = sorted(list(authors.items()),
                                   key=lambda i: i[1][1], reverse=True)[0]
        author_m, author_s = [user.name for user in
                              map(client.get_user, [temp_list_messages[0], temp_list_symbols[0]])]
        channel_info = f'Кол-во сообщений  =>{messages}\n' \
                       f'Кол-во символов  =>{symbols}'
        message_info = f'Чемпион по сообщениям => {author_m}\n' \
                       f'Количество=>{temp_list_messages[1][0]}'
        symbol_info = f'Чемпион по символам =>{author_s} \n' \
                      f'Количество => {temp_list_symbols[1][1]}'
        info_dict = {'Всего за день': '=' * 25, channel_info: '=' * 25,
                     message_info: '=' * 25, symbol_info: '=' * 25}
        for k, v in info_dict.items():
            emb.add_field(name=k, value=v, inline=False)
        await channel.send(embed=emb)