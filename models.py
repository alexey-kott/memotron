import json
import logging
from typing import List, Optional, Tuple

from peewee import Model, TextField, DateTimeField, IntegerField, \
    BooleanField, CompositeKey, DoesNotExist, PostgresqlDatabase, fn
from datetime import datetime, timedelta
from time import sleep

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement

import config

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

db = PostgresqlDatabase(config.DB_NAME,
                        user=config.DB_USER,
                        host=config.DB_HOST,
                        port=config.DB_PORT, autorollback=True)

STORY_INTERVAL = 1  # minutes


class BaseModel(Model):
    class Meta:
        database = db


class Story(BaseModel):
    link = TextField(unique=True)
    title = TextField()
    img_links = TextField(null=True)
    caption = TextField(null=True)
    text = TextField(null=True)
    tags = TextField(null=True)
    author = TextField()
    post_datetime = DateTimeField(null=True)
    scheduled_datetime = DateTimeField(null=True, default=False)
    accepted = BooleanField(null=True, default=None)
    prod_message_id = IntegerField(null=True)
    admin_message_id = IntegerField(null=True)

    def __str__(self):
        return f"{self.title} {self.link}"

    def __repr__(self):
        return f"{self.title} {self.link}"

    @classmethod
    def get_or_create(cls, **kwargs):
        try:
            return cls.get(cls.link == kwargs['link']), False
        except DoesNotExist:
            return cls.create(**kwargs), True

    @classmethod
    def get_last_scheduled_datetime(cls) -> datetime:
        last_scheduled_post = Story.select(fn.Max(Story.scheduled_datetime)).scalar()

        if last_scheduled_post:
            return last_scheduled_post
        else:
            return datetime.now()

    @classmethod
    def get_available_time(cls):
        last_scheduled_post = Story.get_last_scheduled_datetime()
        if last_scheduled_post < datetime.now():
            nearest_available_time = datetime.now() + timedelta(minutes=STORY_INTERVAL)
        else:
            nearest_available_time = last_scheduled_post + timedelta(minutes=STORY_INTERVAL)
        nearest_available_time = nearest_available_time.replace(second=0, microsecond=0)

        return nearest_available_time

    def schedule(self, ):
        """В расписание посто попадает не точно в то время, которое было указано на кнопке,
        а через 20 минут после последнего запланированного поста. Расхождение с временем
        на кнопке может достигать нескольких минут"""
        scheduled_datetime = Story.get_available_time()
        self.scheduled_datetime = scheduled_datetime
        self.save()

    @staticmethod
    def parse_stories(story_items):
        for story_item in story_items:
            try:
                story, is_new_story = Story.parse_story(story_item)
                if not story:
                    continue
                print(story.id)
                story.save()

            except StaleElementReferenceException:
                continue
            except Exception as e:
                print(e)
                pass

    @staticmethod
    def parse_story(story_element) -> Tuple:
        story_id = story_element.get_attribute('data-story-id')
        # if story_id == '_':  # у блоков с рекламой этот атрибут равен '_'
        #     return
        tags = Story.parse_tags(story_element)
        link, title = Story.parse_link(story_element)
        author = Story.parse_author(story_element)
        post_datetime = Story.parse_datetime(story_element)
        img_links = Story.parse_image_links(story_element)
        text = Story.parse_text(story_element)

        if author == 'specials':  # это реклама или иной буллшит
            return None, None
        return Story.get_or_create(link=link,
                                   title=title,
                                   text=text,
                                   tags=tags,
                                   author=author,
                                   img_links=img_links,
                                   scheduled_datetime=None,
                                   post_datetime=post_datetime)

    @staticmethod
    def parse_tags(story_element: WebElement):
        tags = story_element.find_elements_by_class_name("tags__tag")

        return {tag.text for tag in tags}

    @staticmethod
    def parse_link(story_element: WebElement) -> Tuple:
        with open('./parser/story.html', 'w') as file:
            file.write(story_element.get_attribute('outerHTML'))
        # if not story_element.find_elements_by_class_name("story__title-link"):
        #     return

        link = story_element.find_element_by_class_name("story__title-link")
        href = link.get_attribute('href')

        return href, link.text

    @staticmethod
    def parse_author(story_element: WebElement):
        try:
            author = story_element.find_element_by_class_name("user__nick").text
        except NoSuchElementException:
            author = None

        return author

    @staticmethod
    def parse_datetime(story_element: WebElement) -> Optional[datetime]:
        try:
            story_datetime = story_element.find_element_by_class_name("story__datetime")
            str_datetime = story_datetime.get_attribute('datetime')

            story_timestampz = datetime.fromisoformat(str_datetime)
            story_timestamp = story_timestampz.replace(tzinfo=None)
            return story_timestamp
        except NoSuchElementException:
            return None

    @staticmethod
    def parse_image_links(story_element: WebElement) -> List:
        links = []
        image_blocks = story_element.find_elements_by_class_name("story-block_type_image")
        for image_block in image_blocks:
            img = image_block.find_element_by_tag_name('img')
            link = img.get_attribute('src')
            if link is None:
                link: str = img.get_attribute('data-src')

            # TODO: check in future versions [3.11.19]
            # aiogram can't send .webp as image
            # if link.endswith('.webp'):
            #     continue
            links.append(link)

        return json.dumps(links)

    @staticmethod
    def parse_text(story_element: WebElement) -> str:
        text_items = []
        for item in story_element.find_elements_by_class_name("story-block_type_text"):
            text_items.append(item.text)

        return "\n".join(text_items)


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
        self.last_activity = datetime.utcnow()
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
