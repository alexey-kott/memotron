import asyncio
import json
import logging
from asyncio import sleep
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ContentType, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from aiogram.utils import executor
from aiohttp import BasicAuth
import requests
from peewee import fn
from requests.exceptions import ConnectionError

from config import BOT_TOKEN, PROXY_HOST, PROXY_PASS, PROXY_PORT, PROXY_USERNAME, ADMIN_CHANNEL
from models import Story

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

file_handler = logging.FileHandler('info.log')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

try:
    PROXY_AUTH = None
    PROXY_URL = None
    requests.get('https://api.telegram.org', timeout=0.5)
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
    {"id": "25101229880130064",
     "from": {"id": 5844335, "first_name": "Alex", "last_name": "Kott", "username": "AlexKott",
              "language_code": "en"},
     "message": {"message_id": 884, "chat": {"id": -1001143175207, "title": "Memotron Admin Channel",
                                             "username": "memotronadminchannel", "type": "channel"},
                 "date": 1566562356, "photo": [
             {"file_id": "AgADBAADwqkxG4nj9VJ044GDwr2a2zFFqBsABAEAAwIAA20AA1lvAQABFgQ", "file_size": 33270,
              "width": 320,
              "height": 290},
             {"file_id": "AgADBAADwqkxG4nj9VJ044GDwr2a2zFFqBsABAEAAwIAA3gAA1pvAQABFgQ", "file_size": 107941,
              "width": 644, "height": 584}], "caption": "Первый день в школе", "reply_markup": {"inline_keyboard": [
             [{"text": "Schedule at 15:32", "callback_data": "{\"story_id\": 13, \"action\": \"schedule\"}"},
              {"text": "Description on", "callback_data": "{\"story_id\": 13, \"action\": \"description_off\"}"},
              {"text": "Reject", "callback_data": "{\"story_id\": 13, \"action\": \"reject\"}"}]]}},
     "chat_instance": "2309425201251404218", "data": "{\"story_id\": 13, \"action\": \"reject\"}"}

    data = json.loads(callback.data)
    story = Story.get(data['story_id'])
    print(story)
    keyboard = gen_default_keyboard(story)

    if data['action'] == 'reject':
        await bot.delete_message(callback['message']['chat']['id'],
                                 callback['message']['message_id'])
        await callback.answer('Story has been deleted', show_alert=True)

    elif data['action'] == 'schedule':
        pass
    elif data['action'] == 'switch_description':
        await bot.edit_message_caption(ADMIN_CHANNEL,
                                       message_id=story.admin_message_id,
                                       caption='', reply_markup=keyboard)
        await callback.answer('Description removed', show_alert=True)


@dp.message_handler(content_types=[ContentType.TEXT])
async def text_handler(message: Message):
    logger.info(message)


def get_last_scheduled_datetime() -> datetime:
    last_scheduled_post = Story.select(fn.Max(Story.scheduled_datetime)).scalar()

    if last_scheduled_post:
        return datetime.fromisoformat(last_scheduled_post)
    else:
        return datetime.now()


def gen_default_keyboard(story: Story) -> InlineKeyboardMarkup:
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

    callback_data.update({'action': 'description_off'})
    description_button = InlineKeyboardButton('Description on', callback_data=json.dumps(callback_data))

    callback_data.update({'action': 'reject'})
    reject_button = InlineKeyboardButton('Reject', callback_data=json.dumps(callback_data))
    keyboard.row(accept_button, description_button, reject_button)

    return keyboard


async def schedule_new_post(story: Story) -> None:
    img_links = json.loads(story.img_links)


    if len(img_links) == 1:
        response = await bot.send_photo(ADMIN_CHANNEL, photo=img_links[0],
                                        caption=story.title,
                                        reply_markup=keyboard)
        # print(bot_response)
    elif len(img_links) > 1:
        medias = [InputMediaPhoto(url) for url in img_links]

        # text may be added to the message only by
        # adding it to the first item in MediaGroup
        medias[0].caption = story.title

        response = await bot.send_media_group(ADMIN_CHANNEL, medias)
        response = await bot.send_message(ADMIN_CHANNEL, '_',
                                          reply_to_message_id=response[0].message_id,
                                          reply_markup=keyboard)
    else:
        response = await bot.send_message(ADMIN_CHANNEL, story.text,
                                          reply_markup=keyboard, parse_mode='Markdown')

    story.admin_message_id = response['message_id']
    story.save()


async def watch_new_stories() -> None:
    while True:
        unpublished_stories = Story.select().where(Story.published == False,
                                                   Story.text == "",
                                                   Story.admin_message_id.is_null())

        for story in unpublished_stories:
            # await schedule_new_post(story)
            await sleep(1)


if __name__ == "__main__":
    init()
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(watch_new_stories())
    executor.start_polling(dp)
