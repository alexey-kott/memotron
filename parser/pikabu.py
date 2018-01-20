import os
from time import sleep
from datetime import datetime
import locale

from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options

from config import PIKABU_LOGIN, PIKABU_PASSWORD


locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


class PikabuParser:
	def __init__(self):
		pass


	def start(self):
		strt = datetime.now()

		chrome_options = Options()  
		chrome_options.add_argument("--headless")
		chrome_options.add_argument("--start-maximized")
		self.driver = webdriver.Chrome(executable_path=os.path.abspath('./parser/chromedriver/chromedriver'),   chrome_options=chrome_options)  
		self.driver.get("https://pikabu.ru/hot")

		body = self.driver.find_element_by_tag_name("body")

		while not self.is_finish():
			body.send_keys(Keys.END)
			sleep(1)

		page_source = self.driver.page_source
		with open("./parser/page_source.html", "w") as file:
			file.write(page_source)

		stories = Story().parse_stories(self.driver.find_elements_by_class_name("story"))

		self.driver.close()
		fnsh = datetime.now()
		total = fnsh - strt 
		print(total.total_seconds())


	def is_finish(self):
		overflow = self.driver.find_elements_by_class_name("stories__overflow")
		return len(overflow)


class Story:
	tags = {}
	def __init__(link, img_links = [], text = '', tags = {}, author = None, post_datetime = None):
		pass

	@staticmethod
	def parse_stories(stories):
		for story in stories:
			story_id = story.get_attribute('data-story-id')
			if story_id == '_': # у блоков с рекламой этот атрибут равен '_'
				continue
			tags = Story().parse_tags(story)
			if 'реклама' in tags:
				continue
			link, title = Story().parse_link(story)
			author = Story().parse_author(story)
			post_datetime = Story().parse_datetime(story)
			img_links = Story().parse_image_links(story)
		
		Story(link, img_links=img_links, tags=tags, author=author, post_datetime=post_datetime)


	@staticmethod
	def parse_tags(story):
		tags = story.find_elements_by_class_name("story__tag")
		
		return {tag.text for tag in tags}

	@staticmethod
	def parse_link(story):
		link = story.find_element_by_class_name("story__title-link")
		href = link.get_attribute('href')

		return (href, link.text)

	@staticmethod
	def parse_author(story):
		author = story.find_element_by_class_name("story__author")

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

		post_datetime = story.find_element_by_class_name("story__date")
		humanized_datetime = post_datetime.get_attribute('title')
		for month in genitive:
			humanized_datetime = humanized_datetime.replace(month, genitive[month])
		pdt = datetime.strptime(humanized_datetime, '%d %B %Y в %H:%M')

		return post_datetime

	@staticmethod
	def parse_image_links(story):
		links = []
		image_blocks = story.find_elements_by_class_name("b-story-block_type_image")
		for image_block in image_blocks:
			img = image_block.find_element_by_tag_name('img')
			link = img.get_attribute('src')
			if link is None:
				link = img.get_attribute('data-src')
			links.append(link)
		return links
