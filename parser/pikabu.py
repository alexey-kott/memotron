import platform
from logging import getLogger
from pathlib import Path
from time import sleep
from datetime import datetime
import locale
from typing import Set

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# from parser.config import PIKABU_LOGIN, PIKABU_PASSWORD
from selenium.webdriver.remote.webelement import WebElement

from models import Story

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
logger = getLogger()


def get_webdriver_path() -> Path:
    webdriver_paths = {
        'Darwin': Path('./parser/chromedriver/chromedriver_mac'),
        'Linux': Path('./parser/chromedriver/chromedriver_linux'),
    }

    return webdriver_paths[platform.system()]


class Parser:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(executable_path=get_webdriver_path(), chrome_options=chrome_options)
        logger.info('Chrome driver initialized')


class PikabuParser(Parser):
    def run(self):
        start = datetime.now()
        logger.info(f'Start parsing: {start}')

        pikabu_url = "https://pikabu.ru/hot"
        self.driver.get(pikabu_url)
        logger.info(pikabu_url)

        body = self.driver.find_element_by_tag_name("body")

        while not self.is_finish():
            with open("./parser/page_source.html", "w") as file:
                file.write(self.driver.page_source)
            story_containers = self.driver.find_elements_by_class_name("story")
            filtered_story_containers = [story_container for story_container in story_containers
                                         if not PikabuParser.is_trash_story(story_container)]
            Story.parse_stories(filtered_story_containers)

            body.send_keys(Keys.END)
            sleep(1)

        self.driver.close()
        finish = datetime.now()
        total = finish - start
        print(total.total_seconds())

    def is_finish(self):
        overflow = self.driver.find_elements_by_class_name("stories__overflow")
        return len(overflow)

    @classmethod
    def is_trash_story(cls, story_container: WebElement) -> bool:
        """False for adv and other not normal containers"""
        try:
            if story_container.find_elements_by_class_name("story__placeholder"):
                return True
        except StaleElementReferenceException as e:
            return True

        return False


def post_stories(stories: Set[Story]):
    for story in stories:
        post_story(story)


def post_story(story: Story):
    pass
