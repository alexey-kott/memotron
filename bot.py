import re
import threading # для отложенных сообщений
from multiprocessing import Process
from time import sleep
from datetime import datetime, date, time, timedelta
import json
import pprint as ppr

# import sqlite3 as sqlite
import telebot
from telebot import types
from peewee import *
from playhouse.sqlite_ext import *
from playhouse.shortcuts import model_to_dict, dict_to_model # для сериализации peewee-объектов во время логирования ошибок

from config import *
from functions import *
from models import User, Post, Watcher




bot = telebot.TeleBot(token)
bot_id = token.split(":")[0]
# db = SqliteDatabase('db.sqlite3')

pp = ppr.PrettyPrinter(depth = 6)
def pprint(m):
	pp.pprint(m.__dict__)


sid = lambda m: m.chat.id # лямбды для определения адреса ответа
uid = lambda m: m.from_user.id
cid = lambda c: c.message.chat.id


@bot.message_handler(commands = ['init'])
def init(m):
	User.create_table(fail_silently = True)



@bot.message_handler(commands = ['ping'])
def ping(m):
	print(m)
	bot.send_message(sid(m), "I'm alive")


@bot.message_handler(commands = ['start'])
def start(m):
	u = User.cog(m)

@bot.message_handler(content_types = ['text'])
def reply(m):
	u = User.cog(m)
	print(m)
	bot.send_message(prod_channel, m.text)

@bot.message_handler(content_types = ['photo'])
def photo(m):
	u = User.cog(m)
	if u.role == 'user':
		pass
	elif u.role == 'admin':
		keyboard = types.InlineKeyboardMarkup()
		earlier_btn = types.InlineKeyboardButton(text = "Earlier", callback_data = "earlier")
		later_btn = types.InlineKeyboardButton(text = "Later", callback_data = "later")
		post_it_btn = types.InlineKeyboardButton(text = "Post it now!", callback_data = "post_it")
		keyboard.add(earlier_btn, later_btn)
		keyboard.add(post_it_btn)
		info = bot.send_photo(admin_channel, get_file_id(m), reply_markup = keyboard)
		print(info)
	# print(m)




if __name__ == '__main__':
	watcher = Watcher()
	w = Process(target = watcher)
	w.start()
	bot.polling(none_stop=True)
	# while True:
	# 	try:
	# 		bot.polling(none_stop=True)
	# 	except Exception as e:
	# 		print(e)
	# 		sleep(3.5)