from peewee import *
import datetime
from time import sleep

db = SqliteDatabase('db.sqlite3')

sid = lambda m: m.chat.id # лямбды для определения адреса ответа
uid = lambda m: m.from_user.id
cid = lambda c: c.message.chat.id

class BaseModel(Model):
	class Meta:
		database = db


class User(BaseModel):
	user_id			= IntegerField(primary_key = True)
	username 		= TextField()
	first_name		= TextField()
	last_name		= TextField(null = True)
	role			= TextField(default = 'user')
	state 			= TextField(null = True)
	last_activity 	= DateTimeField(null = True)

	def cog(m):
		username = m.from_user.username
		first_name = m.from_user.first_name
		last_name = m.from_user.last_name
		try:
			with db.atomic():
				return User.create(user_id = uid(m), username = username, first_name = first_name, last_name = last_name)
		except Exception as e:
			return User.select().where(User.user_id == uid(m)).get()
			

	def save(self, force_insert=False, only=None):
		self.last_activity = datetime.datetime.utcnow()
		super().save(force_insert, only)

	def set_state(self, state):
		self.state = state
		self.save()


class Post(BaseModel):
	admin_msg_id	  	= IntegerField(unique = True, null = True) # все посты сначала сливаются в закрытый админский канал
	prod_msg_id		  	= IntegerField(unique = True, null = True) # потом автоматически публикуются в основном канале (production)
	likes			  	= IntegerField(default = 0)
	dislikes		  	= IntegerField(default = 0)
	datetime		  	= DateTimeField()
	author 			  	= IntegerField()
	poster			  	= IntegerField()
	published 		  	= BooleanField(default = False)
	perceptual_hash		= TextField(null = True) # perceptual hash, нужен для детекта картинок, которые уже постились: https://habrahabr.ru/post/120562/

	def like(self):
		pass

	def dislike(self):
		pass

	def new_post(m):
		pass
		


class Mark():
	user_id = IntegerField()
	post_id = IntegerField()
	mark 	= IntegerField()

	class Meta:
		primary_key = CompositeKey('user_id', 'post_id')



class Watcher:
	def __call__(self):
		while True:
			pass
			sleep(1)