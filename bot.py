import logging
import asyncio
import aioschedule

from aiogram import Bot, Dispatcher, exceptions
from aiogram.types import Message, Update, BotCommand, CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import BotBlocked

import config
import locales
import database as db
import weather

try:
    import coloredlogs
except ImportError:
    coloredlogs = None

formatter = '{message} | {levelname}'
file_formatter = '{levelname} | {message} | {asctime} | {name} | {lineno}'

log = logging.getLogger('bot')
logging.root.setLevel('DEBUG')
stream_handler = logging.StreamHandler()
stream_handler.formatter = coloredlogs.ColoredFormatter(formatter, style='{') if coloredlogs \
    else logging.Formatter(formatter, style='{')
file_handler = logging.FileHandler('log.txt', 'a')
file_handler.formatter = logging.Formatter(file_formatter, style='{')
logging.root.handlers.clear()
logging.root.addHandler(stream_handler)
logging.root.addHandler(file_handler)
logging.getLogger('aiogram').setLevel('INFO')
logging.getLogger('asyncio').setLevel('INFO')
logging.getLogger('urllib3').setLevel('INFO')
logging.getLogger('aiohhtp').setLevel('INFO')
logging.getLogger('aiohttp.access').setLevel('WARNING')


class MyMiddleware(BaseMiddleware):

    def __init__(self, logger=__name__):
        if not isinstance(logger, logging.Logger):
            logger = logging.getLogger(logger)
        self.logger = logger
        super(MyMiddleware, self).__init__()

    async def on_process_update(self, update: Update, data: dict):
        # self.logger.debug(f'Received update {update}')
        pass

    async def on_pre_process_message(self, message: Message, data: dict):
        # if message.text and message.chat.type != 'private':
        #     await message.answer(locales.only_private)
        #     raise CancelHandler()
        # else:
        user = db.check_user(message)
        self.logger.info(f'{user}: {repr(message.text)}')

    async def on_pre_process_callback_query(self, call: CallbackQuery, data: dict):
        user = call.from_user.username
        user = user or call.from_user.first_name
        self.logger.info(f'{user}: {call.data}')


# infinity
def except_tg_errors(tg_func):
    async def _wrapper(user_id, *args, **kwargs):
        try:
            await tg_func(user_id, *args, **kwargs)
        except exceptions.BotBlocked:
            # log.error(f"Target [ID:{user_id}]: blocked by user")
            return False
        except exceptions.ChatNotFound:
            # log.error(f"Target [ID:{user_id}]: invalid user ID")
            return False
        except exceptions.RetryAfter as e:
            # log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
            await asyncio.sleep(e.timeout)
            return tg_func(user_id, *args, **kwargs)
        except exceptions.UserDeactivated:
            # log.error(f"Target [ID:{user_id}]: user is deactivated")
            return False
        except exceptions.TelegramAPIError as E:
            # log.error(f"Target [ID:{user_id}]: failed with {E}")
            return False
        else:
            # log.debug(f"Target [ID:{user_id}]: success")
            return True

    return _wrapper


@except_tg_errors
async def send_message(user_id: int, text: str, **kwargs):
    await bot.send_message(user_id, text, **kwargs)


@except_tg_errors
async def copy_message(user_id: int, message: Message, **kwargs):
    await message.send_copy(user_id, **kwargs)


@except_tg_errors
async def send_copy(user_id: int, from_chat_id: int, message_id: int, **kwargs):
    await bot.copy_message(user_id, from_chat_id, message_id, **kwargs)


async def weather_broadcast():
    users_with_place = db.users_weather_notifications()
    for user_id, place in users_with_place:
        try:
            await bot.send_message(user_id, weather.current_weather(place))
        except BotBlocked:
            db.subscribe_weather_notifications(user_id)
        except Exception as E:
            log.error('ERROR', E)


async def scheduler():
    aioschedule.every().day.at('9:00').do(weather_broadcast)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    await dp.bot.set_my_commands([
        BotCommand('start', locales.start_command),
        BotCommand('weather', locales.weather_command),
        BotCommand('folder', locales.folder_command),
    ])
    asyncio.create_task(scheduler())


bot = Bot(token=config.bot_token, parse_mode='HTML')
# dp = Dispatcher(bot, storage=MemoryStorage(), run_tasks_by_default=True)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(MyMiddleware('BOT_MIDL'))
