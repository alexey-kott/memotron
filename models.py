from typing import List

from peewee import *
import datetime
from time import sleep

from selenium.common.exceptions import NoSuchElementException

db = SqliteDatabase('db.sqlite3')

sid = lambda m: m.chat.id  # лямбды для определения адреса ответа
uid = lambda m: m.from_user.id
cid = lambda c: c.message.chat.id


class BaseModel(Model):
    class Meta:
        database = db


class Story(BaseModel):
    link = TextField(unique=True)
    img_links = TextField(null=True)
    text = TextField(null=True)
    author = TextField()
    post_date = DateTimeField()

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






# ==================================
class User(BaseModel):
    user_id = IntegerField(primary_key=True)
    username = TextField()
    first_name = TextField()
    last_name = TextField(null=True)
    role = TextField(default='user')
    state = TextField(null=True)
    last_activity = DateTimeField(null=True)

    @staticmethod
    def cog(message):
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        try:
            with db.atomic():
                return User.create(user_id=uid(message), username=username, first_name=first_name, last_name=last_name)
        except Exception as e:
            return User.select().where(User.user_id == uid(message)).get()

    def save(self, force_insert=False, only=None):
        self.last_activity = datetime.datetime.utcnow()
        super().save(force_insert, only)

    def set_state(self, state):
        self.state = state
        self.save()


class Post(BaseModel):
    admin_msg_id = IntegerField(unique=True, null=True)  # все посты сначала сливаются в закрытый админский канал
    prod_msg_id = IntegerField(unique=True, null=True)  # потом автоматически публикуются в основном канале (production)
    likes = IntegerField(default=0)
    dislikes = IntegerField(default=0)
    datetime = DateTimeField()
    author = IntegerField()
    poster = IntegerField()
    published = BooleanField(default=False)
    perceptual_hash = TextField(
        null=True)  # perceptual hash, нужен для детекта картинок, которые уже постились: https://habrahabr.ru/post/120562/

    def like(self):
        pass

    def dislike(self):
        pass

    def new_post(m):
        pass


class Mark(BaseModel):
    user_id = IntegerField()
    post_id = IntegerField()
    mark = IntegerField()

    class Meta:
        primary_key = CompositeKey('user_id', 'post_id')


class Watcher:
    def __call__(self):
        while True:
            pass
            sleep(1)
