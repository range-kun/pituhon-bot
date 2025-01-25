import datetime
import os
import sys
from zoneinfo import ZoneInfo

from loguru import logger

from app.configuration import LOG_LEVEL, LOGGER_OUTPUT, TIME_ZONE

if LOGGER_OUTPUT == "container":
    os.makedirs("logs", exist_ok=True)

log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"

logger.remove()


def set_datetime(record):
    record["extra"]["datetime"] = datetime.datetime.now(ZoneInfo(TIME_ZONE))


logger.configure(patcher=set_datetime)

if LOGGER_OUTPUT == "std_err":
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format=log_format,
        backtrace=False,
        diagnose=False,
    )
elif LOGGER_OUTPUT == "container":
    logger.add(
        "logs/log-{time:YYYY-MM-DD}.log",
        rotation="12:00",
        retention="1 week",
        level=LOG_LEVEL,
        format=log_format,
        backtrace=False,
        diagnose=False,
    )
else:
    logger.add(sys.stderr, level="ERROR", format=log_format)
    logger.error(f"Invalid LOGGER_OUTPUT: {LOGGER_OUTPUT}. Defaulting to stderr.")
