import asyncio
from logging import getLogger

from parser.pikabu import PikabuParser
from parser.pikabu import Story

logger = getLogger()

if __name__ == "__main__":
    logger.info("Start parsing...")
    Story.create_table(safe=True)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(PikabuParser().run())
