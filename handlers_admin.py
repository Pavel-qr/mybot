import datetime
import re
from typing import List

from aiogram import exceptions, Dispatcher
from aiogram.dispatcher.filters import Text, CommandStart
from aiogram.types import Message, CallbackQuery, ContentType, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import config
import locales
import keyboards
import database as db
import vk
from bot import dp, send_message, copy_message
from handlers_user import view_files


class Admin(StatesGroup):
    saw_user = State()
    admin_answer = State()
    mail = State()


# admin menu
@dp.message_handler(lambda message: message.text.lower() in ('/a', '/а', '/admin', 'admin', 'админ'),
                    user_id=config.admins,
                    state='*')
async def hi_admin(message: Message, state: FSMContext):
    await state.finish()
    # await message.answer('start', reply_markup=keyboards.back('start'))
    await message.answer('Привет, админ!', reply_markup=keyboards.admin())


@dp.callback_query_handler(text='admin', user_id=config.admins, state='*')
async def hi_admin_call(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    await call.message.answer('Привет, админ!', reply_markup=keyboards.admin())


@dp.message_handler(text=locales.users_button, user_id=config.admins)
async def chose_users(message: Message):
    users = db.all_users()
    keyboard = ReplyKeyboardMarkup()
    for user in users:
        keyboard.add(user.identifiable_str())
    await message.answer('Выбери пользователя:', reply_markup=keyboard)
    await Admin.saw_user.set()


@dp.message_handler(state=Admin.saw_user, user_id=config.admins)
async def saw_user(message: Message):
    user = db.all_users(message.text.split('_')[1])
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Написать', callback_data=f'contact_answer_{user.user_id}_'))
    keyboard.add(InlineKeyboardButton(text='Файлы', callback_data=f'view_{user.user_id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='admin'))
    await message.answer(user.account(), reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('view_'), user_id=config.admins, state=Admin.saw_user)
async def admin_view_files(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await view_files(call)


@dp.message_handler(text=locales.statistic_button, user_id=config.admins)
async def send_message_to_all(message: Message):
    users = db.all_users()
    await message.answer(f'В боте {len(users)} пользователей!', reply_markup=keyboards.admin())


@dp.message_handler(text=locales.mail_button, user_id=config.admins)
async def send_message_to_all(message: Message):
    await Admin.mail.set()
    await message.answer('Ответ пиши', reply_markup=keyboards.back('admin'))


@dp.message_handler(state=Admin.mail, content_types=ContentType.ANY, user_id=config.admins)
async def mail_to_all(message: Message, state: FSMContext):
    users = db.all_users()
    c_send = 0
    c_not = 0
    for u in users:
        msg = await copy_message(u.user_id, message)
        if msg:
            c_send += 1
        else:
            c_not += 1
    await message.answer(f'Ok: {c_send}, not ok: {c_not}', reply_markup=keyboards.admin())
    await state.set_state()


@dp.callback_query_handler(Text(startswith='contact'), state='*')
async def admin_answer(call: CallbackQuery, state: FSMContext):
    action, user_id, message_id = call.data.split('_')[1:]
    if action == 'answer':
        await Admin.admin_answer.set()
        await state.update_data(user_id=user_id, message_id=message_id)
        await call.message.answer('Ответ пиши', reply_markup=keyboards.back())
    elif action == 'thanks':
        msg = await send_message(user_id, 'Спасибо за обращение\n'
                                          'Мы с этим что-нибудь сделаем',
                                 reply_to_message_id=message_id)
        await call.message.answer('Okay' if msg else 'Error', reply_markup=keyboards.back())


@dp.message_handler(state=Admin.admin_answer, content_types=ContentType.ANY)
async def admin_answer_send(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.finish()
    user_id = data['user_id']
    message_id = data['message_id']
    msg = await send_message(user_id, 'Спасибо за обращение\n'
                                      'Мы с этим что-нибудь сделаем',
                             reply_to_message_id=message_id)
    await message.answer('Okay' if msg else 'Error', reply_markup=keyboards.back())


@dp.message_handler(text=locales.vk_button, user_id=config.admins)
async def vk_spy(message: Message):
    statuses = vk.get_status(db.vk_user_id(message.chat.id), check_status, message.chat.id)
    async for status in statuses:
        await message.answer(status)


@dp.message_handler(commands='vkid', user_id=config.admins)
async def vk_spy(message: Message):
    db.change_vk(message.chat.id, 'online_user_id', message.text[6:])
    await message.answer('ok')


def check_status(param, status=True):
    return db.check_weather_notifications(param) == status

# def register_admin(dp: Dispatcher):
#     dp.register_message_handler(admin_menu, Text(('/a', '/а', '/admin'), ignore_case=True),
#                                 state='*', user_id=config.admins)
#     dp.register_message_handler(admin_menu, CommandStart(deep_link='a'),
#                                 state='*', user_id=config.admins)
#     dp.register_message_handler(saw_user, state=Admin.saw_user)
#     dp.register_message_handler(edit_message, content_types=ContentType.ANY, state=Admin.edit)
#     dp.register_message_handler(add_message, content_types=ContentType.ANY, state=Admin.add)
#     dp.register_message_handler(admin_answer_send, content_types=ContentType.ANY, state=Admin.admin_answer)
#     dp.register_message_handler(mail_to_all, content_types=ContentType.ANY, state=Admin.mail)
# 
#     dp.register_callback_query_handler(admin_call, Text('admin'), state='*')
#     dp.register_callback_query_handler(edit_call, Text(startswith='edit'))
#     dp.register_callback_query_handler(add_call, Text(startswith='add'))
#     dp.register_callback_query_handler(delete_call, Text(startswith='delete'))
#     # dp.register_callback_query_handler(chose_users, Text('users'))
#     dp.register_callback_query_handler(admin_answer, Text(startswith='answer_'))
#     dp.register_callback_query_handler(statistic, Text('statistic'))
#     dp.register_callback_query_handler(send_message_to_all, Text('mail'))
#     dp.register_callback_query_handler(admin_settings, Text('admin_settings'))
