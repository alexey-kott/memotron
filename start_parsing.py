from logging import getLogger

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from parser.pikabu import PikabuParser
from parser.pikabu import Story

logger = getLogger()

if __name__ == "__main__":
    logger.info("Start parsing...")
    Story.create_table(fail_silently=True)
    PikabuParser().run()
