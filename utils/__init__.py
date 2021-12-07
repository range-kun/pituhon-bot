from datetime import datetime, timedelta



def yesterday():
    return datetime.date(datetime.now() - timedelta(days=1))


def today():
    return datetime.date(datetime.now())

async def send_data_for_day_to_db(self):
    await self.bot.wait_until_ready()
    channel = self.bot.get_channel(698975367326728352)  # test mode
    # channel = client.get_channel(MAIN_CHANNEL_ID)    #run mode
    while not self.bot.is_closed():
        conn, cur = db()
        if self.messages:
            await logs.send_data_for_day(channel, self.bot)
            logs.update_stats_author_day(conn, cur)
        await logs.send_data_schedule(cur, channel, self.bot)
        logs.update_stats_schedule(cur)
        conn.commit()
        conn.close()

        self.messages, self.symbols, self.authors = 0, 0, {}