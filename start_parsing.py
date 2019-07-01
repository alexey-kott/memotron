from sqlalchemy import create_engine
from sqlalchemy.orm import  sessionmaker

from parser.pikabu import PikabuParser

# PikabuParser().run()
from parser.pikabu import Story
story = Story(name='djnckd')

engine = create_engine('sqlite:///memotron.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()
session.add(story)
session.commit()
session.close()
