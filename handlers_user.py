import asyncio

from aiogram.types import Message, CallbackQuery, ContentType
from aiogram import Dispatcher
from random import randint, choice
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import config
import locales
import keyboards
import database as db
from bot import bot, dp

import weather
import memes
import edit_img
import ttt
import image


class User(StatesGroup):
    add = State()
    weather_place = State()
    contact_admin = State()


# user menu
@dp.message_handler(commands=['start', 'help'], state='*')
async def start_message(message: Message, state: FSMContext):
    await state.finish()
    await message.answer(locales.start_message, reply_markup=keyboards.main())


@dp.callback_query_handler(text='start', state='*')
async def start_call(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    await call.message.answer(locales.menu_message, reply_markup=keyboards.main())


@dp.message_handler(text=locales.mem_button)
async def send_mem(message: Message):
    img = memes.photo(memes.memes)
    await message.answer_photo(img)
    memes.memes = memes.update_links(db.memes_id(message.chat.id))


@dp.message_handler(text=locales.cat_button)
async def send_cat(message: Message):
    img = memes.photo(memes.cats)
    await message.answer_photo(img)
    memes.cats = memes.update_links(config.cats_id)


@dp.message_handler(text=locales.space_button)
async def space(message: Message):
    img = edit_img.crop_random('img/milky_way.jpg')
    await message.answer_photo(img)


@dp.message_handler(text=locales.fate_button)
async def rand(message: Message):
    await message.answer('Что кидаем?', reply_markup=keyboards.rand())


@dp.callback_query_handler(Text(startswith='rand'))
async def rand_call(call: CallbackQuery):
    action = call.data.split('_')[1]
    if action == 'coin':
        value = randint(1, 1000)
        if value in (1, 2):
            result = 'Ребро'
            img = image.coin_edge
        elif value < 502:
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


@dp.message_handler(text=locales.weather_button)
@dp.message_handler(commands='weather')
async def check_weather(message: Message):
    await message.answer('Где хочешь узнать погоду?\n'
                         'Напиши страну или город\n'
                         'Или присылай свое гео',
                         reply_markup=keyboards.weather(db.last_weather(message.chat.id)))
    await User.weather_place.set()


@dp.message_handler(state=User.weather_place)
async def weather_place(message: Message, state: FSMContext):
    await state.finish()
    db.last_weather_update(message.chat.id, message.text)
    await message.answer(weather.current_weather(message.text),
                         reply_markup=keyboards.main())


@dp.message_handler(content_types=ContentType.LOCATION, state=User.weather_place)
@dp.message_handler(content_types=ContentType.LOCATION)
async def weather_location(message: Message, state: FSMContext):
    await state.finish()
    await message.answer(weather.weather_at_location(message.location),
                         reply_markup=keyboards.main())


@dp.message_handler(text=locales.folder_button)
@dp.message_handler(commands='folder')
async def open_folder(message: Message):
    await message.answer('Ты можешь сохранить здесь свои файлы и посмотреть их позже',
                         reply_markup=keyboards.open(message.chat.id))


@dp.callback_query_handler(text='add')
async def add_file(call: CallbackQuery):
    await User.add.set()
    await call.message.edit_text('Отправь файл')


@dp.message_handler(content_types=ContentType.PHOTO, state=User.add)
async def add_photo(message: Message):
    db.add_file(message.chat.id, message.photo[0].file_id, 'photo')
    await message.answer('Успешно', reply_markup=keyboards.back())


@dp.message_handler(content_types=ContentType.VIDEO, state=User.add)
async def add_video(message: Message):
    db.add_file(message.chat.id, message.video.file_id, 'video')
    await message.answer('Успешно', reply_markup=keyboards.back())


@dp.message_handler(content_types=ContentType.DOCUMENT, state=User.add)
async def add_document(message: Message):
    db.add_file(message.chat.id, message.document.file_id, 'document')
    await message.answer('Успешно', reply_markup=keyboards.back())


@dp.message_handler(content_types=ContentType.AUDIO, state=User.add)
async def add_document(message: Message):
    db.add_file(message.chat.id, message.audio.file_id, 'audio')
    await message.answer('Успешно', reply_markup=keyboards.back())


@dp.message_handler(content_types=ContentType.ANY, state=User.add)
async def wrong_file(message: Message):
    await message.answer('Неверный формат', reply_markup=keyboards.back())


@dp.callback_query_handler(lambda call: call.data.startswith('view'))
async def view_files(call: CallbackQuery):
    await call.message.edit_text('Твои файлы')
    files = db.view_files(call.data.split('_')[1])
    funcs = {
        'photo': call.message.answer_photo,
        'video': call.message.answer_video,
        'document': call.message.answer_document,
        'audio': call.message.answer_audio,
    }
    for file in files:
        await funcs[file.file_type](file.tg_id, reply_markup=keyboards.file(file.file_id))


@dp.callback_query_handler(lambda call: call.data.startswith('delete'))
async def delete_files(call: CallbackQuery):
    await call.message.delete()
    db.delete_file(call.data.split('_')[1])
    await call.message.answer('Готово')


@dp.message_handler(text=locales.ttt_button)
async def tic_tac_toe(message: Message, state: FSMContext):
    p_let = choice(('x', 'o'))
    if p_let == 'x':
        b_let = 'o'
        board = [[' ', ' ', ' '],
                 [' ', ' ', ' '],
                 [' ', ' ', ' ']]
    else:
        b_let = 'x'
        board = [[b_let, ' ', ' '],
                 [' ', ' ', ' '],
                 [' ', ' ', ' ']]
    await state.update_data(board=board, p_let=p_let, b_let=b_let)
    await message.answer('Твой ход!', reply_markup=keyboards.ttt(board))


@dp.callback_query_handler(Text('ttt'))
async def ttt_start_call(call: CallbackQuery, state: FSMContext):
    await tic_tac_toe(call.message, state)
    await call.message.delete()


@dp.callback_query_handler(Text(startswith='board'))
async def ttt_call(call: CallbackQuery, state: FSMContext):
    row, column = map(int, call.data.split('_')[1:])
    data = await state.get_data()
    board = data['board']
    p_let = data['p_let']
    b_let = data['b_let']
    if ttt.is_empty(board, row, column):
        await call.answer()
        board[row][column] = p_let
        if ttt.is_win(board, p_let):
            return await call.message.edit_text('Ты победил)', reply_markup=keyboards.ttt(board, 'ttt_end'))
        elif ttt.is_full(board):
            return await call.message.edit_text('Ничья', reply_markup=keyboards.ttt(board, 'ttt_end'))
        row1, column1 = ttt.computer_turn(board, b_let, p_let)
        board[row1][column1] = b_let
        if ttt.is_win(board, b_let):
            return await call.message.edit_text('Ты проиграл(', reply_markup=keyboards.ttt(board, 'ttt_end'))
        if ttt.is_full(board):
            return await call.message.edit_text('Ничья', reply_markup=keyboards.ttt(board, 'ttt_end'))
    else:
        return await call.answer('Поле занято')
    await state.update_data(board=board, p_let=p_let, b_let=b_let)
    await call.message.edit_reply_markup(reply_markup=keyboards.ttt(board))


@dp.callback_query_handler(Text(startswith='ttt_end'))
async def ttt_call(call: CallbackQuery):
    await call.answer('Игра окончена')


@dp.message_handler(text=locales.notification_button)
@dp.message_handler(text='🔔')
async def weather_notifications(message: Message):
    await message.answer('Подпишись и получай прогноз погоды каждое утро',
                         reply_markup=keyboards.notifications(db.check_weather_notifications(message.chat.id)))


@dp.callback_query_handler(Text(startswith='subscribe'))
async def weather_notifications_call(call: CallbackQuery):
    await call.answer()
    action = call.data.split('_')[1]
    db.subscribe_weather_notifications(call.message.chat.id)
    await call.message.edit_reply_markup(reply_markup=keyboards.notifications(action == 'on'))


@dp.message_handler(text=locales.admin_button)
async def contact_admin(message: Message):
    await message.answer('Пиши сюда свои предложения по развитию бота или информацию о замеченных ошибках\n',
                         reply_markup=keyboards.back())
    await User.contact_admin.set()


@dp.message_handler(state=User.contact_admin, content_types=ContentType.ANY)
async def contact_admin_send(message: Message, state: FSMContext):
    await state.finish()
    await message.forward(config.admin)
    await bot.send_message(config.admin,
                           f'Сообщение от @{message.from_user.username} | <code>{message.from_user.id}</code>\n'
                           'Что делать?', 
                           reply_markup=keyboards.admin_answer(message.from_user.id, message.message_id))
    await message.answer('Сообщение отправлено', reply_markup=keyboards.main())


@dp.message_handler(text=locales.game_button)
async def dice(message: Message):
    await message.answer('Во что играем?', reply_markup=keyboards.games())


@dp.callback_query_handler(Text(startswith='games'))
async def casino(call: CallbackQuery):
    await call.message.delete()
    action = call.data.split('_')[1]
    actions = {
        'dice': '',
        'casino': '🎰',
        'darts': '🎯',
        'bowling': '🎳',
        'basketball': '🏀',
        'football': '⚽',
    }
    await call.message.answer_dice(actions.get(action, ''))


@dp.message_handler()
async def echo(message: Message):
    await message.answer(locales.unknown_message, reply_markup=keyboards.main())


@dp.message_handler(content_types=['photo'])
async def echo_photo(message: Message):
    await message.answer(locales.beauty_message)
    await asyncio.sleep(3)
    await message.answer_photo(message.photo[0].file_id)

# def register_user(dp: Dispatcher):
#     dp.register_message_handler(start_message, commands=['start'], state='*')
#     dp.register_callback_query_handler(start_call, Text('menu'), state='*')
#
#
# def register_last(dp: Dispatcher):
#     dp.register_message_handler(echo, state='*')
#     dp.register_callback_query_handler(all_calls)
