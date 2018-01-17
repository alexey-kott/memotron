import os
from time import sleep

from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options

from config import PIKABU_LOGIN, PIKABU_PASSWORD


class PikabuParser:
	def __init__(self):
		pass


	def start():
		chrome_options = Options()  
		# chrome_options.add_argument("--headless")
		driver = webdriver.Chrome(executable_path=os.path.abspath('./parser/chromedriver/chromedriver'),   chrome_options=chrome_options)  
		driver.get("https://pikabu.ru/hot")

		body = driver.find_element_by_tag_name("body")
		for i in range(10):
			body.send_keys(Keys.END)
			sleep(1)


		driver.close()

