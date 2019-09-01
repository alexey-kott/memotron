import platform
from pathlib import Path
from time import sleep
from datetime import datetime
import locale
from typing import Set

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# from parser.config import PIKABU_LOGIN, PIKABU_PASSWORD
from models import Story

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


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


class PikabuParser(Parser):
    def run(self):
        start = datetime.now()

        self.driver.get("https://pikabu.ru/hot")

        body = self.driver.find_element_by_tag_name("body")

        while not self.is_finish():
            with open("./parser/page_source.html", "w") as file:
                file.write(self.driver.page_source)
            Story.parse_stories(self.driver.find_elements_by_class_name("story"))

            body.send_keys(Keys.END)
            sleep(1)

        self.driver.close()
        finish = datetime.now()
        total = finish - start
        print(total.total_seconds())

    def is_finish(self):
        overflow = self.driver.find_elements_by_class_name("stories__overflow")
        return len(overflow)


def post_stories(stories: Set[Story]):
    for story in stories:
        post_story(story)


def post_story(story: Story):
    pass
