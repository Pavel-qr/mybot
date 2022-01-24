import logging
from random import randint, choice
import asyncio
import aioschedule

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import ContentType

import config
from weather import current_weather
import vk
import memes
import edit_img
import my_orm
import keyboards
import ttt
import image

bot = Bot(token=config.bot_token, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())

formater = '{asctime} | {filename} | {lineno} | {message}'
# logging.basicConfig(filename='bot.log', filemode='w', level=logging.INFO, format=formater)
logging.basicConfig(level=logging.INFO, style="{", format=formater)


class MyMiddleware(BaseMiddleware):
    """
    Simple middleware
    """
    def __init__(self, logger=__name__):
        if not isinstance(logger, logging.Logger):
            logger = logging.getLogger(logger)
        self.logger = logger
        super(MyMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        """
        This handler is called when dispatcher receives a message

        :param message:
        """
        self.logger.info(f'{message.from_user.username}, {message.text}')


dp.middleware.setup(MyMiddleware())


class User(StatesGroup):
    weather_place = State()
    contact_admin = State()
    admin_answer = State()


# user menu
@dp.message_handler(commands=['start', 'help'], state='*')
async def start_message(message: types.Message, state: FSMContext):
    my_orm.check_user(message.chat.id, message.from_user.username)
    await state.finish()
    await message.answer('Привет!\n', reply_markup=keyboards.main)


@dp.callback_query_handler(text='start', state='*')
async def start_call(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    await call.message.answer('Привет!\n', reply_markup=keyboards.main)


@dp.message_handler(lambda message: message.text.lower() in ('мем', 'mem'))
async def send_mem(message: types.Message):
    img = memes.vk_group_photo(memes.memes)
    await message.answer_photo(img)
    memes.cats = memes.update_links(config.cb_id)


@dp.message_handler(lambda message: message.text.lower().startswith('кот'))
async def send_cat(message: types.Message):
    img = memes.vk_group_photo(memes.cats)
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
async def weather(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.add(my_orm.last_weather(message.chat.id))
    await message.answer('Где хочешь узнать погоду?\n'
                         'Напиши страну или город\n',
                         reply_markup=keyboard)
    await User.weather_place.set()


@dp.message_handler(state=User.weather_place)
async def weather_place(message: types.Message, state: FSMContext):
    await state.finish()
    my_orm.last_weather_update(message.chat.id, message.text)
    await message.answer(current_weather(message.text),
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
            await call.message.edit_text('Вы победили', reply_markup=keyboard)
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
            await call.message.edit_text('Вы проиграли', reply_markup=keyboard)
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
    if my_orm.users_weather_notifications(message.chat.id):
        keyboard.add(types.InlineKeyboardButton(text='Отписаться', callback_data='subscribe_off'))
    else:
        keyboard.add(types.InlineKeyboardButton(text='Подписаться', callback_data='subscribe_on'))
    keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await message.answer('Подпишись и получай прогноз погоды каждое утро',
                         reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith='subscribe'))
async def weather_notifications_call(call: types.CallbackQuery):
    action = call.data.split('_')[1]
    keyboard = types.InlineKeyboardMarkup()
    if action == 'on':
        my_orm.subscribe_weather_notifications(call.message.chat.id)
        keyboard.add(types.InlineKeyboardButton(text='Отписаться', callback_data='subscribe_off'))
    else:
        my_orm.subscribe_weather_notifications(call.message.chat.id, 'off')
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


@dp.callback_query_handler(Text(startswith='contact'))
async def admin_answer(call: types.CallbackQuery, state: FSMContext):
    action, userid, message_id = call.data.split('_')[1:]
    if action == 'answer':
        await User.admin_answer.set()
        await state.update_data(userid=userid, message_id=message_id)
        await call.message.answer('Ответ пиши', reply_markup=keyboards.back())
    elif action == 'thanks':
        await call.message.answer('Okay', reply_markup=keyboards.back())
        await bot.send_message(userid, 'Спасибо за обращение\n'
                                       'Мы с этим что-нибудь сделаем', reply_to_message_id=message_id)


@dp.message_handler(state=User.admin_answer, content_types=ContentType.ANY)
async def admin_answer_send(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    userid = data['userid']
    message_id = data['message_id']
    await bot.send_message(userid, 'Вот что мы сделаем:', reply_to_message_id=message_id)
    await message.forward(userid)
    await message.answer('Сообщение отправлено', reply_markup=keyboards.main)


# admin menu
@dp.message_handler(lambda message: message.text.lower() in ('admin', 'админ') and message.chat.id in config.admins)
async def hi_admin(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Привет, админ!', reply_markup=keyboards.admin)


@dp.message_handler(lambda message: message.text.lower() in ('кости', 'dice'))
async def dice(message: types.Message):
    await message.answer_dice()
    # await message.answer_dice('🎯')
    # await message.answer_dice('🎳')
    # await message.answer_dice('⚽')
    # await message.answer_dice('🏀')


@dp.message_handler(lambda message: message.text.lower() in ('казино', 'casino'))
async def casino(message: types.Message):
    await message.answer_dice('🎰')


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer('Когда-нибудь я скажу тебе всё, что думаю...\n\n\n'
                         'А пока используй кнопки')


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
    users = my_orm.users_weather_notifications()
    for i in users:
        place = my_orm.last_weather(i)
        await bot.send_message(i, current_weather(place))


async def scheduler():
    aioschedule.every().day.at('9:00').do(weather_broadcast)
    # aioschedule.every(5).seconds.do(weather_broadcast)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
