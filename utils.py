from datetime import timedelta, datetime
from pathlib import Path
from typing import Collection

import aiofiles
from PIL import Image
from aiogram.types import InputMediaPhoto
from aiohttp import ClientSession
from yarl import URL

from models import Story

STORY_INTERVAL = 20  # minutes


async def download_file(file_link: str) -> Path:
    tmp_dir = Path('/tmp')
    file_url = URL(file_link)
    file_path = tmp_dir / file_url.name
    async with ClientSession() as session:
        async with session.get(file_url) as response:
            async with aiofiles.open(file_path, 'wb') as file:
                await file.write(await response.read())

                return file_path


def webp_to_png(webp_file_path: Path) -> Path:
    img = Image.open(webp_file_path)
    img.convert('RGBA')
    png_file_path = webp_file_path.parent / (webp_file_path.stem + '.png')
    img.save(png_file_path, 'png')

    return png_file_path


async def prepare_media(links: Collection[str]):
    media = []
    for link in links:
        file_url = URL(link)
        file_name = Path(file_url.name)
        if file_name.suffix == '.webp':
            webp_file_path = await download_file(link)
            png_file_path = webp_to_png(webp_file_path)

            file = open(png_file_path, 'rb')
            input_media = InputMediaPhoto(file)
            media.append(input_media)

            webp_file_path.unlink()
            png_file_path.unlink()
        else:
            media.append(InputMediaPhoto(link))

        if len(media) == 10:
            return media

    return media


def get_schedule_button_text(story: Story) -> str:
    """If story is not scheduled we offer the nearest available time,
    in other way we display scheduled time"""
    if story.scheduled_datetime:
        story_time = story.scheduled_datetime
        scheduled_flag = '✅'
    else:
        story_time = Story.get_available_time()
        scheduled_flag = ''

    schedule_button_text = f'🗓 {story_time.strftime("%H:%M")} {scheduled_flag}'

    return schedule_button_text
