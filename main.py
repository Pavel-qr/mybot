import logging
import coloredlogs
from random import randint, choice
import asyncio
import aioschedule

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.files import MemoryStorage
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import ContentType
from aiogram.utils.exceptions import BotBlocked

import config
import database as db
import weather
import vk
import memes
import edit_img
import keyboards
import ttt
import image

bot = Bot(token=config.bot_token, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())

formatter = '{asctime} | {name} | {lineno} | {message}'

log = logging.getLogger("main")
# logging.root.setLevel("DEBUG")
logging.root.setLevel("INFO")
stream_handler = logging.StreamHandler()
if coloredlogs is not None:
    stream_handler.formatter = coloredlogs.ColoredFormatter(formatter, style="{")
else:
    stream_handler.formatter = logging.Formatter(formatter, style="{")
logging.root.handlers.clear()
logging.root.addHandler(stream_handler)
logging.getLogger("aiogram").setLevel("INFO")
logging.getLogger("asyncio").setLevel("INFO")
logging.getLogger("urllib3").setLevel("INFO")


class MyMiddleware(BaseMiddleware):
    """
    Simple middleware
    """

    def __init__(self, logger='mybot'):
        if not isinstance(logger, logging.Logger):
            logger = logging.getLogger(logger)
        self.logger = logger
        self.counter = 0
        super(MyMiddleware, self).__init__()

    async def on_process_update(self, update: types.Update, data: dict):
        self.logger.debug(f"Received update {update}")

    async def on_pre_process_message(self, message: types.Message, data: dict):
        user = db.check_user(message)
        self.logger.info(f'{user}: {message.text}')


dp.middleware.setup(MyMiddleware())


class User(StatesGroup):
    weather_place = State()
    contact_admin = State()
    admin_answer = State()
    saw_user = State()


# user menu
@dp.message_handler(commands=['start', 'help'], state='*')
async def start_message(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Привет!', reply_markup=keyboards.main)


@dp.callback_query_handler(text='start', state='*')
async def start_call(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    await call.message.answer('Привет!', reply_markup=keyboards.main)


@dp.message_handler(lambda message: message.text.lower() in ('мем', 'mem'))
async def send_mem(message: types.Message):
    img = memes.photo(memes.memes)
    await message.answer_photo(img)
    memes.memes = memes.update_links(db.memes_id(message.from_user.id))


@dp.message_handler(lambda message: message.text.lower().startswith('кот'))
async def send_cat(message: types.Message):
    img = memes.photo(memes.cats)
    await message.answer_photo(img)
    memes.cats = memes.update_links(config.cats_id)


@dp.message_handler(lambda message: message.text.lower() in ('space', 'космос'))
async def space(message: types.Message):
    img = edit_img.crop_random('img/milky_way.jpg')
    await message.answer_photo(img)


@dp.message_handler(lambda message: message.text.lower() == 'отдаю свою судьбу в чужие руки')
async def rand(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Монетка', callback_data='rand_coin'),
                 types.InlineKeyboardButton(text='Кубик', callback_data='rand_dice'))
    keyboard.add(types.InlineKeyboardButton(text='Случайное число от 1 до 100', callback_data='rand_number'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await message.answer('Что кидаем?', reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith='rand'))
async def rand_call(call: types.CallbackQuery):
    action = call.data.split('_')[1]
    if action == 'coin':
        value = randint(1, 1000)
        if value in (1, 2):
            result = 'Ребро'
            img = image.coin_edge
        elif value < 501:
            result = 'Решка'
            img = image.coin_tail
        else:
            result = 'Орел'
            img = image.coin_head
        await call.message.answer_photo(img, result, reply_markup=keyboards.back('Ещё раз', 'rand_coin'))
    elif action == 'dice':
        await call.message.answer_photo(image.dice[randint(1, 6)],
                                        reply_markup=keyboards.back('Ещё раз', 'rand_dice'))
    elif action == 'number':
        await call.message.answer(str(randint(1, 100)), reply_markup=keyboards.back('Ещё раз', 'rand_number'))
    await call.message.delete()


@dp.message_handler(lambda message: message.text.lower() in ('weather', 'погода'))
async def check_weather(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.add(db.last_weather(message.chat.id))
    # keyboard.add(types.KeyboardButton('Отправить местоположение 🗺️', request_location=True))
    await message.answer('Где хочешь узнать погоду?\n'
                         'Напиши страну или город\n',
                         reply_markup=keyboard)
    await User.weather_place.set()


@dp.message_handler(state=User.weather_place)
async def weather_place(message: types.Message, state: FSMContext):
    await state.finish()
    db.last_weather_update(message.chat.id, message.text)
    await message.answer(weather.current_weather(message.text),
                         reply_markup=keyboards.main)


@dp.message_handler(content_types=types.ContentTypes.LOCATION, state=User.weather_place)
async def weather_location(message: types.Message, state: FSMContext):
    await state.finish()
    logging.info(message.location.latitude)
    logging.info(message.location.longitude)
    await message.answer(weather.weather_at_location(message.location),
                         reply_markup=keyboards.main)


@dp.message_handler(lambda message: message.text.lower() in ('крестики', 'нолики', 'крестики-нолики'))
async def tic_tac_toe(message: types.Message, state: FSMContext):
    if message.text.lower() == 'крестики-нолики':
        message.text = choice(('крестики', 'нолики'))
    if message.text.lower() == 'крестики':
        p_let = 'x'
        b_let = 'o'
        board = [[' ', ' ', ' '],
                 [' ', ' ', ' '],
                 [' ', ' ', ' ']]
    else:
        p_let = 'o'
        b_let = 'x'
        board = [[b_let, ' ', ' '],
                 [' ', ' ', ' '],
                 [' ', ' ', ' ']]
    await state.update_data(board=board, p_let=p_let, b_let=b_let)
    keyboard = types.InlineKeyboardMarkup()
    for i in range(3):
        keyboard.add(types.InlineKeyboardButton(text=board[i][0], callback_data=f'board_{i}_0'),
                     types.InlineKeyboardButton(text=board[i][1], callback_data=f'board_{i}_1'),
                     types.InlineKeyboardButton(text=board[i][2], callback_data=f'board_{i}_2'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await message.answer('Твой ход!', reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith='board'))
async def ttt_call(call: types.CallbackQuery, state: FSMContext):
    row, column = map(int, call.data.split('_')[1:])
    data = await state.get_data()
    board = data['board']
    p_let = data['p_let']
    b_let = data['b_let']
    if ttt.is_empty(board, row, column):
        await call.answer()
        board[row][column] = p_let
        if ttt.is_win(board, p_let):
            keyboard = types.InlineKeyboardMarkup()
            for i in range(3):
                keyboard.add(types.InlineKeyboardButton(text=board[i][0], callback_data=f'ttt_end_{i}_0'),
                             types.InlineKeyboardButton(text=board[i][1], callback_data=f'ttt_end_{i}_1'),
                             types.InlineKeyboardButton(text=board[i][2], callback_data=f'ttt_end_{i}_2'))
            keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
            await call.message.edit_text('Ты победил)', reply_markup=keyboard)
            return
        if ttt.is_full(board):
            keyboard = types.InlineKeyboardMarkup()
            for i in range(3):
                keyboard.add(types.InlineKeyboardButton(text=board[i][0], callback_data=f'ttt_end_{i}_0'),
                             types.InlineKeyboardButton(text=board[i][1], callback_data=f'ttt_end_{i}_1'),
                             types.InlineKeyboardButton(text=board[i][2], callback_data=f'ttt_end_{i}_2'))
            keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
            await call.message.edit_text('Ничья', reply_markup=keyboard)
            return
        row1, column1 = ttt.computer_turn(board, b_let, p_let)
        board[row1][column1] = b_let
        if ttt.is_win(board, b_let):
            keyboard = types.InlineKeyboardMarkup()
            for i in range(3):
                keyboard.add(types.InlineKeyboardButton(text=board[i][0], callback_data=f'ttt_end_{i}_0'),
                             types.InlineKeyboardButton(text=board[i][1], callback_data=f'ttt_end_{i}_1'),
                             types.InlineKeyboardButton(text=board[i][2], callback_data=f'ttt_end_{i}_2'))
            keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
            await call.message.edit_text('Ты проиграл(', reply_markup=keyboard)
            return
        if ttt.is_full(board):
            keyboard = types.InlineKeyboardMarkup()
            for i in range(3):
                keyboard.add(types.InlineKeyboardButton(text=board[i][0], callback_data=f'ttt_end_{i}_0'),
                             types.InlineKeyboardButton(text=board[i][1], callback_data=f'ttt_end_{i}_1'),
                             types.InlineKeyboardButton(text=board[i][2], callback_data=f'ttt_end_{i}_2'))
            keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
            await call.message.edit_text('Ничья', reply_markup=keyboard)
            return
    else:
        await call.answer('Поле занято')
        return
    await state.update_data(board=board, p_let=p_let, b_let=b_let)
    keyboard = types.InlineKeyboardMarkup()
    for i in range(3):
        keyboard.add(types.InlineKeyboardButton(text=board[i][0], callback_data=f'board_{i}_0'),
                     types.InlineKeyboardButton(text=board[i][1], callback_data=f'board_{i}_1'),
                     types.InlineKeyboardButton(text=board[i][2], callback_data=f'board_{i}_2'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await call.message.edit_reply_markup(reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith='ttt_end'))
async def ttt_call(call: types.CallbackQuery):
    await call.answer('Игра окончена')


@dp.message_handler(lambda message: message.text.lower() in ('🔔',))
async def weather_notifications(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    if db.check_weather_notifications(message.chat.id):
        keyboard.add(types.InlineKeyboardButton(text='Отписаться', callback_data='subscribe_off'))
    else:
        keyboard.add(types.InlineKeyboardButton(text='Подписаться', callback_data='subscribe_on'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await message.answer('Подпишись и получай прогноз погоды каждое утро',
                         reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith='subscribe'))
async def weather_notifications_call(call: types.CallbackQuery):
    await call.answer()
    action = call.data.split('_')[1]
    keyboard = types.InlineKeyboardMarkup()
    if action == 'on':
        db.subscribe_weather_notifications(call.message.chat.id)
        keyboard.add(types.InlineKeyboardButton(text='Отписаться', callback_data='subscribe_off'))
    else:
        db.subscribe_weather_notifications(call.message.chat.id)
        keyboard.add(types.InlineKeyboardButton(text='Подписаться', callback_data='subscribe_on'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await call.message.edit_reply_markup(reply_markup=keyboard)


@dp.message_handler(lambda message: message.text.lower() == 'связь с администрацией')
async def contact_admin(message: types.Message):
    await message.answer('Пиши сюда свои предложения по развитию бота или информацию о замеченных ошибках\n',
                         reply_markup=keyboards.back())
    await User.contact_admin.set()


@dp.message_handler(state=User.contact_admin, content_types=ContentType.ANY)
async def contact_admin_send(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Ответить', callback_data=f'contact_answer_{message.from_user.id}'
                                                                           f'_{message.message_id}'))
    keyboard.add(types.InlineKeyboardButton(text='Спасибо за обращение', callback_data=f'contact_thanks_'
                                                                                       f'{message.from_user.id}'
                                                                                       f'_{message.message_id}'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await message.forward(config.admin)
    await bot.send_message(config.admin,
                           f'Сообщение от @{message.from_user.username} | <code>{message.from_user.id}</code>\n'
                           'Что делать?', reply_markup=keyboard)
    await message.answer('Сообщение отправлено', reply_markup=keyboards.main)


@dp.callback_query_handler(Text(startswith='contact'), state='*')
async def admin_answer(call: types.CallbackQuery, state: FSMContext):
    action, user_id, message_id = call.data.split('_')[1:]
    if action == 'answer':
        await User.admin_answer.set()
        await state.update_data(user_id=user_id, message_id=message_id)
        await call.message.answer('Ответ пиши', reply_markup=keyboards.back())
    elif action == 'thanks':
        try:
            await call.message.answer('Okay', reply_markup=keyboards.back())
            await bot.send_message(user_id, 'Спасибо за обращение\n'
                                            'Мы с этим что-нибудь сделаем', reply_to_message_id=message_id)
        except:
            await call.message.answer('Bot is blocked', reply_markup=keyboards.back())


@dp.message_handler(state=User.admin_answer, content_types=ContentType.ANY)
async def admin_answer_send(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    user_id = data['user_id']
    message_id = data['message_id']
    try:
        await bot.send_message(user_id, message.text, reply_to_message_id=message_id)
        await message.answer('Сообщение отправлено', reply_markup=keyboards.main)
    except:
        await message.answer('Bot is blocked', reply_markup=keyboards.back())


@dp.message_handler(lambda message: message.text.lower() == 'игры')
async def dice(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Кости', callback_data='games_dice'),
                 types.InlineKeyboardButton(text='Казино', callback_data='games_casino'))
    keyboard.add(types.InlineKeyboardButton(text='Дартс', callback_data='games_darts'),
                 types.InlineKeyboardButton(text='Боулинг', callback_data='games_bowling'))
    keyboard.add(types.InlineKeyboardButton(text='Баскетбол', callback_data='games_basketball'),
                 types.InlineKeyboardButton(text='Футбол', callback_data='games_football'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await message.answer('Во что играем?', reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith='games'))
async def casino(call: types.CallbackQuery):
    await call.message.delete()
    action = call.data.split('_')[1]
    if action == 'dice':
        await call.message.answer_dice('')
    elif action == 'casino':
        await call.message.answer_dice('🎰')
    elif action == 'darts':
        await call.message.answer_dice('🎯')
    elif action == 'bowling':
        await call.message.answer_dice('🎳')
    elif action == 'basketball':
        await call.message.answer_dice('🏀')
    elif action == 'football':
        await call.message.answer_dice('⚽')


# admin menu
@dp.message_handler(lambda message: message.text.lower() in ('/a', '/а', '/admin', 'admin', 'админ'), user_id=config.admins,
                    state='*')
async def hi_admin(message: types.Message, state: FSMContext):
    await state.finish()
    # await message.answer('start', reply_markup=keyboards.back('start'))
    await message.answer('Привет, админ!', reply_markup=keyboards.admin)


@dp.callback_query_handler(text='admin', user_id=config.admins, state='*')
async def hi_admin_call(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    await call.message.answer('Привет, админ!', reply_markup=keyboards.admin)


@dp.message_handler(text='Пользователи', user_id=config.admins)
async def chose_users(message: types.Message):
    users = db.all_users()
    keyboard = types.ReplyKeyboardMarkup()
    for user in users:
        keyboard.add(user.identifiable_str())
    await message.answer('Выбери пользователя:', reply_markup=keyboard)
    await User.saw_user.set()


@dp.message_handler(state=User.saw_user, user_id=config.admins)
async def saw_user(message: types.Message):
    user = db.all_users(message.text.split('_')[1])
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Написать', callback_data=f'contact_answer_{user.id}_'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='admin'))
    await message.answer(user.account(), reply_markup=keyboard)


@dp.message_handler(text='Статистика', user_id=config.admins)
async def send_message_to_all(message: types.Message):
    users = db.all_users()
    await message.answer(f'В боте {len(users)} пользователей!', reply_markup=keyboards.admin)


@dp.message_handler(text='Рассылка', user_id=config.admins)
async def send_message_to_all(message: types.Message):
    # users = db.all_users()
    await message.answer('In development!', reply_markup=keyboards.admin)


@dp.message_handler(text='ВК', user_id=config.admins)
async def vk_spy(message: types.Message):
    statuses = vk.get_status(db.vk_user_id(message.chat.id), check_status, message.chat.id)
    async for status in statuses:
        await message.answer(status)


@dp.message_handler(commands='vkid', user_id=config.admins)
async def vk_spy(message: types.Message):
    db.change_vk(message.chat.id, 'online_user_id', message.text[6:])
    await message.answer('ok')


def check_status(param, status=True):
    return db.check_weather_notifications(param) == status


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer('Когда-нибудь я скажу тебе всё, что думаю...\n\n\n'
                         'А пока используй кнопки', reply_markup=keyboards.main)


@dp.message_handler(content_types=['photo'])
async def echo_photo(message: types.Message):
    await message.answer('Красиво. Я тоже так хочу😯')
    await asyncio.sleep(3)
    await message.answer_photo(message.photo[0].file_id)


# infinity
async def broadcast(message, users):
    for i in users:
        await bot.send_message(i, message)


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
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
