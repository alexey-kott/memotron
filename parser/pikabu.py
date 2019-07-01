import platform
from pathlib import Path
from time import sleep
from datetime import datetime
import locale
from typing import List, Set, Tuple

import attr
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine, Column, Integer, Unicode
from sqlalchemy.ext.declarative import declarative_base

# from parser.config import PIKABU_LOGIN, PIKABU_PASSWORD

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
Base = declarative_base()


class Story(Base):

    # def __init__(self, link, img_links=[], text='', tags: Set = set(), author=None, post_datetime=None):
    #     print(link, img_links, text, tags, author, post_datetime)
    #     pass
    __tablename__ = 'story'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)

    def __init__(self, name):
        self.name = name

    @staticmethod
    def parse_stories(story_items):
        for story in story_items:
            story_id = story.get_attribute('data-story-id')
            if story_id == '_':  # у блоков с рекламой этот атрибут равен '_'
                continue
            tags = Story.parse_tags(story)
            if 'реклама' in tags:
                continue
            link, title = Story.parse_link(story)
            author = Story.parse_author(story)
            post_datetime = Story.parse_datetime(story)
            img_links = Story.parse_image_links(story)

            Story(link, img_links=img_links, tags=tags, author=author, post_datetime=post_datetime)

    @staticmethod
    def parse_tags(story):
        tags = story.find_elements_by_class_name("story__tag")

        return {tag.text for tag in tags}

    @staticmethod
    def parse_link(story) -> Tuple:
        with open('./parser/story.html', 'w') as file:
            file.write(story.get_attribute('outerHTML'))
        link = story.find_element_by_class_name("story__title-link")
        href = link.get_attribute('href')

        return href, link.text

    @staticmethod
    def parse_author(story):
        try:
            author = story.find_element_by_class_name("story__author")
        except NoSuchElementException:
            author = None

        return author

    @staticmethod
    def parse_datetime(story):
        genitive = {
            'января': 'январь',
            'февраля': 'февраль',
            'марта': 'март',
            'апреля': 'апрель',
            'мая': 'май',
            'июня': 'июнь',
            'июля': 'июль',
            'августа': 'август',
            'сентября': 'сентябрь',
            'октября': 'октябрь',
            'ноября': 'ноябрь',
            'декабря': 'декабрь'
        }
        try:
            post_datetime = story.find_element_by_class_name("story__date")
            humanized_datetime = post_datetime.get_attribute('title')
            for month in genitive:
                humanized_datetime = humanized_datetime.replace(month, genitive[month])
            pdt = datetime.strptime(humanized_datetime, '%d %B %Y в %H:%M')
        except NoSuchElementException:
            post_datetime = None

        return post_datetime

    @staticmethod
    def parse_image_links(story) -> List:
        links = []
        image_blocks = story.find_elements_by_class_name("b-story-block_type_image")
        for image_block in image_blocks:
            img = image_block.find_element_by_tag_name('img')
            link = img.get_attribute('src')
            if link is None:
                link = img.get_attribute('data-src')
            links.append(link)
        return links

engine = create_engine('sqlite:///memotron.db', echo=True)
Base.metadata.create_all(engine)


def get_webdriver_path() -> Path:
    webdriver_paths = {
        'Darwin': Path('./parser/chromedriver/chromedriver_mac'),
        'Linux': Path('./parser/chromedriver/chromedriver_linux'),
    }

    return webdriver_paths[platform.system()]


class Parser:
    def __init__(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(executable_path=get_webdriver_path(), chrome_options=chrome_options)


class PikabuParser(Parser):
    def run(self):
        start = datetime.now()

        self.driver.get("https://pikabu.ru/hot")

        body = self.driver.find_element_by_tag_name("body")

        while not self.is_finish():
            with open("./parser/page_source.html", "w") as file:
                file.write(self.driver.page_source)
            try:
                Story.parse_stories(self.driver.find_elements_by_class_name("story"))
            except:
                pass

            body.send_keys(Keys.END)
            sleep(1)

        self.driver.close()
        finish = datetime.now()
        total = finish - start
        print(total.total_seconds())

    def is_finish(self):
        overflow = self.driver.find_elements_by_class_name("stories__overflow")
        return len(overflow)
