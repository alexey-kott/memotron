import asyncio
import json
import logging
from asyncio import sleep
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ContentType, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from aiogram.utils import executor
from aiogram.utils.exceptions import ToMuchMessages
from aiohttp import BasicAuth
import requests
from peewee import fn
from requests.exceptions import ConnectionError

from config import BOT_TOKEN, PROXY_HOST, PROXY_PASS, PROXY_PORT, PROXY_USERNAME, ADMIN_CHANNEL, MEMOTRON_CHANNEL
from models import Story

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

file_handler = logging.FileHandler('info.log')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

try:
    PROXY_AUTH = None
    PROXY_URL = None
    requests.get('https://api.telegram.org', timeout=1)
except ConnectionError as e:
    PROXY_URL = f"socks5://{PROXY_HOST}:{PROXY_PORT}"
    PROXY_AUTH = BasicAuth(login=PROXY_USERNAME, password=PROXY_PASS)

bot = Bot(token=BOT_TOKEN, proxy=PROXY_URL, proxy_auth=PROXY_AUTH)
dp = Dispatcher(bot)


def init():
    Story.create_table(fail_silently=True)


@dp.message_handler(commands=['ping'])
async def ping_handler(message: Message):
    await message.reply("I'm alive")


@dp.callback_query_handler()
async def callback_handler(callback: CallbackQuery):
    print(callback)

    {"id": "25101228074669798",
     "from": {"id": 5844335, "is_bot": False, "first_name": "Alex", "last_name": "Kott", "username": "AlexKott",
              "language_code": "en"}, "message": {"message_id": 1039,
                                                  "chat": {"id": -1001143175207, "title": "Memotron Admin Channel",
                                                           "username": "memotronadminchannel", "type": "channel"},
                                                  "date": 1566944811,
                                                  "photo": [
                                                      {
                                                          "file_id": "AgADBAADIKoxG_A35FImcdwKC2G_EFecoBsABAEAAwIAA20AA7_sAAIWBA",
                                                          "file_size": 29539, "width": 320,
                                                          "height": 320},
                                                      {
                                                          "file_id": "AgADBAADIKoxG_A35FImcdwKC2G_EFecoBsABAEAAwIAA3gAA8DsAAIWBA",
                                                          "file_size": 123092, "width": 700,
                                                          "height": 700}], "caption": "Машина подходит",
                                                  "reply_markup": {"inline_keyboard": [
                                                      [{"text": "Schedule at 01:46",
                                                        "callback_data": "{\"story_id\": 215, \"action\": \"schedule\"}"},
                                                       {"text": "Description on",
                                                        "callback_data": "{\"story_id\": 215, \"action\": \"switch_description\"}"},
                                                       {"text": "Reject",
                                                        "callback_data": "{\"story_id\": 215, \"action\": \"reject\"}"}]]}},
     "chat_instance": "2309425201251404218", "data": "{\"story_id\": 215, \"action\": \"switch_description\"}"}

    {"id": "25101228614166194",
     "from": {"id": 5844335, "is_bot": False, "first_name": "Alex", "last_name": "Kott", "username": "AlexKott",
              "language_code": "en"},
     "message": {"message_id": 1039, "chat": {"id": -1001143175207, "title": "Memotron Admin Channel",
                                              "username": "memotronadminchannel", "type": "channel"},
                 "date": 1566944811, "edit_date": 1566944898, "photo": [
             {"file_id": "AgADBAADIKoxG_A35FImcdwKC2G_EFecoBsABAEAAwIAA20AA7_sAAIWBA", "file_size": 29539, "width": 320,
              "height": 320},
             {"file_id": "AgADBAADIKoxG_A35FImcdwKC2G_EFecoBsABAEAAwIAA3gAA8DsAAIWBA", "file_size": 123092,
              "width": 700,
              "height": 700}], "reply_markup": {"inline_keyboard": [
             [{"text": "Schedule at 01:48", "callback_data": "{\"story_id\": 215, \"action\": \"schedule\"}"},
              {"text": "Description on", "callback_data": "{\"story_id\": 215, \"action\": \"switch_description\"}"},
              {"text": "Reject", "callback_data": "{\"story_id\": 215, \"action\": \"reject\"}"}]]}},
     "chat_instance": "2309425201251404218", "data": "{\"story_id\": 215, \"action\": \"switch_description\"}"}

    data = json.loads(callback.data)
    story = Story.get(data['story_id'])
    print(story)
    keyboard = get_default_keyboard(story)

    if data['action'] == 'reject':
        await bot.delete_message(callback['message']['chat']['id'],
                                 callback['message']['message_id'])
        await callback.answer('Story has been deleted')

    elif data['action'] == 'schedule':
        pass
    elif data['action'] == 'switch_description':
        if callback.message.caption:
            caption = None
        else:
            caption = story.title
        await bot.edit_message_caption(ADMIN_CHANNEL,
                                       message_id=story.admin_message_id,
                                       caption=caption, reply_markup=keyboard)
        if caption:
            await callback.answer('Description returned')
        else:
            await callback.answer('Description removed')


@dp.message_handler(content_types=[ContentType.TEXT])
async def text_handler(message: Message):
    logger.info(message)


def get_last_scheduled_datetime() -> datetime:
    last_scheduled_post = Story.select(fn.Max(Story.scheduled_datetime)).scalar()

    if last_scheduled_post:
        return last_scheduled_post
    else:
        return datetime.now()


def get_default_keyboard(story: Story) -> InlineKeyboardMarkup:
    """ Default keyboard consists three button: Schedule, Description on/off, Reject"""
    post_interval = 20  # minutes
    keyboard = InlineKeyboardMarkup()
    callback_data = {
        'story_id': story.id,
        'action': 'schedule'
    }

    last_scheduled_post = get_last_scheduled_datetime()
    nearest_free_time = last_scheduled_post + timedelta(minutes=post_interval)
    accept_button = InlineKeyboardButton(f'Schedule at {nearest_free_time.strftime("%H:%M")}',
                                         callback_data=json.dumps(callback_data))

    callback_data.update({'action': 'switch_description'})
    description_button = InlineKeyboardButton('Description on', callback_data=json.dumps(callback_data))

    callback_data.update({'action': 'reject'})
    reject_button = InlineKeyboardButton('Reject', callback_data=json.dumps(callback_data))
    keyboard.row(accept_button, description_button, reject_button)

    return keyboard


def get_scheduled_keyboard(story: Story):
    keyboard = InlineKeyboardMarkup()
    callback_data = {
        'story_id': story.id,
        'action': 'earlier'
    }

    earlier_button = InlineKeyboardButton(f'Earlier ⬇️',
                                          callback_data=json.dumps(callback_data))

    callback_data.update({'action': 'post_now'})
    post_now_button = InlineKeyboardButton(f'Post it now',
                                           callback_data=json.dumps(callback_data))

    callback_data.update({'action': 'later'})
    later_button = InlineKeyboardButton(f'Later ⬆️',
                                        callback_data=json.dumps(callback_data))

    keyboard.row(earlier_button, post_now_button, later_button)

    return keyboard


async def schedule_new_post(story: Story) -> None:
    img_links = json.loads(story.img_links)
    keyboard = get_default_keyboard(story)

    if len(img_links) == 1:
        response = await bot.send_photo(ADMIN_CHANNEL, photo=img_links[0],
                                        caption=story.title,
                                        reply_markup=keyboard)
        # print(bot_response)
    elif len(img_links) > 1:
        media = [InputMediaPhoto(url) for url in img_links]

        # text may be added to the message only by
        # adding it to the first item in MediaGroup
        # medias[0].caption = story.title
        if len(media) > 10:
            return

        response = await bot.send_media_group(ADMIN_CHANNEL, media)
        response = await bot.send_message(ADMIN_CHANNEL, story.title,
                                          reply_to_message_id=response[0].message_id,
                                          reply_markup=keyboard)
    else:
        response = await bot.send_message(ADMIN_CHANNEL, story.title,
                                          reply_markup=keyboard, parse_mode='Markdown')

    story.admin_message_id = response['message_id']
    story.save()


async def watch_new_stories() -> None:
    while True:
        unpublished_stories = Story.select().where(Story.published == False,
                                                   Story.text == "",
                                                   Story.admin_message_id.is_null())

        for story in unpublished_stories:
            await schedule_new_post(story)
            await sleep(1)
        await sleep(1)


async def schedule_trigger():
    while True:
        now = datetime.now()
        now = now.replace(microsecond=0)
        for story in Story.select().where(Story.scheduled_datetime == now,
                                          Story.published == False):

            img_links = json.loads(story.img_links)

            if len(img_links) == 1:
                bot_response = await bot.send_photo(MEMOTRON_CHANNEL,
                                                    photo=img_links[0],
                                                    caption=story.title)
                print(bot_response)
            elif len(img_links) > 1:
                medias = [InputMediaPhoto(url) for url in img_links]

                if len(medias) > 10:  # TG limit
                    return

                bot_response = await bot.send_media_group(MEMOTRON_CHANNEL, medias)
                print(bot_response)

            story.published = True
            story.save()

            await sleep(1)
        await sleep(1)


async def update_keyboards() -> None:
    while True:
        for story in Story.select().where(Story.scheduled_datetime.is_null()):
            keyboard = get_default_keyboard(story)
            await bot.edit_message_reply_markup(ADMIN_CHANNEL,
                                                message_id=story.admin_message_id,
                                                reply_markup=keyboard)

            await sleep(1)
        await sleep(1)


if __name__ == "__main__":
    init()
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(watch_new_stories())
    asyncio.ensure_future(schedule_trigger())
    asyncio.ensure_future(update_keyboards())
    executor.start_polling(dp)
