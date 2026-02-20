from pydantic_settings import BaseSettings
from loguru import logger
import os


class Settings(BaseSettings):
    LOG_LEVEL: str
    LOG_FILE: str


class CrawlerSettings(Settings):
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/crawler.log"


class AppSettings(Settings):
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"


def setup_logging(settings: Settings):
    log_folder = "logs"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    logger.remove()
    logger.add(
        settings.LOG_FILE,
        rotation="100 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level=settings.LOG_LEVEL
    )