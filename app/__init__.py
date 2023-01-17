import sys

from app import configuration
from app import log


def get_notification_channel(bot_mode: str | None = None) -> int | None:
    if bot_mode == "test":
        channel_id = configuration.TEST_CHANNEL_ID or configuration.MAIN_CHANNEL_ID or None
    else:
        channel_id = configuration.MAIN_CHANNEL_ID or None

    if channel_id:
        log.logger.info(f"Notification will be send to channel with id {channel_id}")
    else:
        log.logger.info("Notification channel not selected")
    return channel_id


try:
    mode = sys.argv[1]
except IndexError:
    NOTIFICATION_CHANNEL = get_notification_channel()
else:
    if mode == "test" and configuration.TEST_TOKEN:
        TOKEN = configuration.TEST_TOKEN
        NOTIFICATION_CHANNEL = get_notification_channel("test")