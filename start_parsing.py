from sqlalchemy import create_engine
from sqlalchemy.orm import  sessionmaker

from parser.pikabu import PikabuParser
from parser.pikabu import Story

Story.create_table(fail_silently=True)
PikabuParser().run()
