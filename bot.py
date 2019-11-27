import json
import asyncio
import logging
from asyncio import sleep
from datetime import datetime

import requests
from aiohttp import BasicAuth
from requests.exceptions import ConnectionError
from aiogram import Bot, Dispatcher
from aiogram.utils import executor
from aiogram.utils.exceptions import MessageToEditNotFound, MessageNotModified
from aiogram.types import (Message, ContentType, InlineKeyboardMarkup,
                           InlineKeyboardButton, CallbackQuery, InputMediaPhoto)

from models import Story
from utils import prepare_media, get_schedule_button_text
from config import (PROXY_HOST, PROXY_PORT, PROXY_USERNAME, PROXY_PASS,
                    BOT_TOKEN, ADMIN_CHANNEL, MEMOTRON_CHANNEL)

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
    logger.debug(callback)

    data = json.loads(callback.data)
    story = Story.get(data['story_id'])

    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']

    if data['action'] == 'reject':
        await bot.delete_message(chat_id, message_id)
        await callback.answer('Story has been deleted')

    elif data['action'] == 'schedule':
        story.schedule()
        keyboard = get_story_keyboard(story)
        await callback.answer(f'Story scheduled at {story.scheduled_datetime}')
        await bot.edit_message_reply_markup(chat_id, message_id=message_id,
                                            reply_markup=keyboard)
    elif data['action'] == 'switch_description':
        if callback.message.caption:
            caption = None
        else:
            caption = story.title

        keyboard = get_story_keyboard(story)
        await bot.edit_message_caption(chat_id, message_id=message_id,
                                       caption=caption, reply_markup=keyboard)
        if caption:
            await callback.answer('Description returned')
        else:
            await callback.answer('Description removed')

        story.caption = caption
        story.save()


@dp.message_handler(content_types=[ContentType.TEXT])
async def text_handler(message: Message):
    logger.info(message)


def get_story_keyboard(story: Story) -> InlineKeyboardMarkup:
    """ Default keyboard consists three button: Schedule, Description on/off, Reject"""
    keyboard = InlineKeyboardMarkup()
    callback_data = {
        'story_id': story.id,
        'action': 'schedule'
    }

    schedule_button_text = get_schedule_button_text(story)
    schedule_button = InlineKeyboardButton(schedule_button_text,
                                           callback_data=json.dumps(callback_data))

    callback_data.update({'action': 'switch_description'})
    description_button = InlineKeyboardButton('📋', callback_data=json.dumps(callback_data))

    callback_data.update({'action': 'reject'})
    reject_button = InlineKeyboardButton('❌', callback_data=json.dumps(callback_data))
    keyboard.row(schedule_button, description_button, reject_button)

    return keyboard


async def schedule_new_post(story: Story) -> None:
    img_links = json.loads(story.img_links)
    keyboard = get_story_keyboard(story)

    if len(img_links) == 1:
        response = await bot.send_photo(ADMIN_CHANNEL, photo=img_links[0],
                                        caption=story.title,
                                        reply_markup=keyboard)
    elif len(img_links) > 1:
        media = await prepare_media(img_links)

        # text may be added to the message only by
        # adding it to the first item in MediaGroup
        media[0].caption = story.title

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
        unpublished_stories = Story.select().where(Story.admin_message_id.is_null(),
                                                   Story.text == "")

        for story in unpublished_stories:
            await schedule_new_post(story)
            await sleep(1)
        await sleep(1)


async def schedule_trigger():
    while True:
        now = datetime.now()
        now = now.replace(second=0, microsecond=0)
        for story in Story.select().where(Story.scheduled_datetime == now,
                                          Story.prod_message_id == None):
            img_links = json.loads(story.img_links)

            if len(img_links) == 1:
                response = await bot.send_photo(MEMOTRON_CHANNEL,
                                                photo=img_links[0],
                                                caption=story.title)

            elif len(img_links) > 1:
                medias = [InputMediaPhoto(url) for url in img_links]
                if len(medias) > 10:  # TG limit
                    return

                response = await bot.send_media_group(MEMOTRON_CHANNEL, medias)
                response = response[0]
            else:
                response = await bot.send_message(MEMOTRON_CHANNEL, text=story.text)
            logger.info(response)
            story.prod_message_id = response['message_id']
            story.save()

            await sleep(1)
        await sleep(1)


async def update_keyboards() -> None:
    """Updates message keyboards in admin channel"""
    while True:
        for story in Story.select().\
                           where(Story.scheduled_datetime.is_null()).\
                           order_by(Story.post_datetime.desc()):
            keyboard = get_story_keyboard(story)
            try:
                await bot.edit_message_reply_markup(ADMIN_CHANNEL,
                                                    message_id=story.admin_message_id,
                                                    reply_markup=keyboard)
            except (MessageToEditNotFound, MessageNotModified) as e:
                logger.debug(e)
            await sleep(3)


if __name__ == "__main__":
    init()
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(watch_new_stories())
    asyncio.ensure_future(schedule_trigger())
    asyncio.ensure_future(update_keyboards())
    executor.start_polling(dp)
