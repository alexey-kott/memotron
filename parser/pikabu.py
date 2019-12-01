import asyncio
import platform
import logging
from pathlib import Path
from time import sleep
from datetime import datetime
import locale
from typing import Set

from selenium.webdriver import Chrome
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from proxybroker import Broker, Proxy

# from parser.config import PIKABU_LOGIN, PIKABU_PASSWORD
from selenium.webdriver.remote.webelement import WebElement

from models import Story

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def get_webdriver_path() -> Path:
    webdriver_paths = {
        'Darwin': Path('./parser/chromedriver/chromedriver_mac'),
        'Linux': Path('./parser/chromedriver/chromedriver_linux'),
    }

    return webdriver_paths[platform.system()]


class PikabuParser:
    PIKABU_URL = "https://pikabu.ru/hot"
    STORY_LIMIT = 1300
    proxies = asyncio.Queue()
    driver = None

    def init_driver(self, proxy: Proxy = None):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--start-maximized")
        if proxy:
            options.add_argument(f'--proxy-server={proxy.host}:{proxy.port}')
        self.driver = Chrome(executable_path=get_webdriver_path(), options=options)

    async def prepare_proxy(self) -> None:
        broker = Broker(self.proxies)
        await broker.find(types=['HTTP', 'HTTPS'])

    def start_parsing(self) -> None:
        self.driver.get(self.PIKABU_URL)

        body = self.driver.find_element_by_tag_name("body")

        counter = 0
        while counter < self.STORY_LIMIT:
            with open("./parser/page_source.html", "w") as file:
                file.write(self.driver.page_source)
            story_containers = self.driver.find_elements_by_class_name("story")
            if not story_containers:
                logger.warning("Page was not received")
                return
            filtered_story_containers = [story_container for story_container in story_containers
                                         if not PikabuParser.is_trash_story(story_container)]
            counter += Story.parse_stories(filtered_story_containers)
            body.send_keys(Keys.END)
            sleep(1)
        self.driver.close()

    async def run(self):
        logger.info(f'Parser launch: {datetime.now()}')
        await self.prepare_proxy()

        while True:
            proxy = None
            if self.check_availability():
                proxy = await self.proxies.get()
                logger.info(f'Get proxy: {proxy}')
            self.init_driver(proxy)
            logger.info('Chrome driver initialized')
            logger.info(f'New WebDriver instance: {datetime.now()}')
            self.start_parsing()
            logger.info(f'WebDriver instance stop: {datetime.now()}')

    @classmethod
    def is_trash_story(cls, story_container: WebElement) -> bool:
        """False for adv and other not normal containers"""
        try:
            if story_container.find_elements_by_class_name("story__placeholder"):
                return True
        except StaleElementReferenceException:
            return True

        return False

    def check_availability(self) -> bool:
        self.init_driver()
        self.driver.get(self.PIKABU_URL)
        try:
            if self.driver.title.find('403') != -1:
                return False
            if self.driver.find_element_by_tag_name('body').get_attribute('innerText') == '':  # if empty body
                return False
            return True
        finally:
            self.driver.close()
