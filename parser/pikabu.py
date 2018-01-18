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

		# while not self.is_finish():
		# 	body.send_keys(Keys.END)
		# 	sleep(1)

		# page_source = driver.page_source
		# with open("./parser/page_source.html", "w") as file:
		# 	file.write(page_source)

		stories = Story().parse_stories(self.driver.find_elements_by_class_name("story"))

		# for story in stories:
			# print(story)

		# sleep(999)
		self.driver.close()
		fnsh = datetime.now()
		total = fnsh - strt 
		print(total.total_seconds())


	def is_finish(self):
		overflow = self.driver.find_elements_by_class_name("stories__overflow")
		return len(overflow)


class Story:
	tags = {}
	def __init__(link, pictures = {}, text = {}, tags = {}, author = None, post_datetime = None):
		pass

	@staticmethod
	def parse_stories(stories):
		for story in stories:
			tags = Story().parse_tags(story)
			link, title = Story().parse_link(story)
			author = Story().parse_author(story)
			post_datetime = Story().parse_datetime(story)


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
		post_datetime = story.find_element_by_class_name("story__date")
		humanized_datetime = post_datetime.get_attribute('title')
		pdt = datetime.strptime(humanized_datetime, '%d %B %Y в %H:%M')
		print(humanized_datetime)
		print(pdt, end='\n\n')

		return post_datetime