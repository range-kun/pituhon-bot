import sys

from loguru import logger

from app.configuration import LOGGER_OUTPUT

log_format = "{time:YYYY-MM-DD HH:mm:ss UTCZ} | {level} | {name}:{function}() | {message} | " \
             "at file {file} with line {line}"
logger.remove()

if LOGGER_OUTPUT == "std_err":
    logger.add(
        sys.stderr,
        level="DEBUG",
        format=log_format,
        backtrace=False,
        diagnose=False
    )
elif LOGGER_OUTPUT == "container":
    logger.add(
        f"logs/log-{{time:YYYY-MM-DD}}.log",
        rotation="12:00",
        retention="1 week",
        level="INFO",
        format=log_format,
        backtrace=False,
        diagnose=False
    )
