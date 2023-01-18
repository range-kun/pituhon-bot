from collections import defaultdict

from discord import User
from discord.ext import tasks


class YouTubeLinksCounter:

    def __init__(self):
        self.youtube_limits: dict[int, int] = defaultdict(int)
        self.max_youtube_limit = None

    def set_youtube_link_limit(self, limit: int | None):
        self.max_youtube_limit = limit

    def is_in_limit(self, user: User) -> bool:
        if not self.max_youtube_limit:
            return True
        user_sent_links = self.youtube_limits[user.id]
        if user_sent_links >= self.max_youtube_limit:
            return False
        self.youtube_limits[user.id] += 1
        return True

    @tasks.loop(minutes=60)
    async def set_limits_to_zero(self):
        self.youtube_limits = defaultdict(int)


youtube_links_counter = YouTubeLinksCounter()
