from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton

import locales


def main():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(locales.weather_button, locales.folder_button)
    keyboard.row(locales.space_button, locales.mem_button, locales.cat_button)
    keyboard.row(locales.ttt_button, locales.game_button)
    keyboard.row(locales.notification_button, '🔔')
    keyboard.row(locales.fate_button)
    keyboard.row(locales.admin_button)
    return keyboard


def admin():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(locales.statistic_button, locales.mail_button)
    keyboard.row(locales.vk_button, locales.users_button)
    return keyboard


def admin_answer(user_id, message_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        text='Ответить',
        callback_data=f'contact_answer_{user_id}_{message_id}'))
    keyboard.add(InlineKeyboardButton(
        text='Спасибо за обращение',
        callback_data=f'contact_thanks_{user_id}_{message_id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='start'))
    return keyboard


def open(chat_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Добавить', callback_data='add'),
                 InlineKeyboardButton(text='Посмотреть', callback_data=f'view_{chat_id}'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='start'))
    return keyboard


def file(file_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Удалить', callback_data=f'delete_{file_id}'))
    # keyboard.add(InlineKeyboardButton(text='Назад', callback_data='start'))
    return keyboard


def weather(place):
    keyboard = ReplyKeyboardMarkup()
    keyboard.add(place)
    keyboard.add(KeyboardButton('Отправить местоположение 🗺️', request_location=True))
    return keyboard


def ttt(board, prefix='board'):
    keyboard = InlineKeyboardMarkup()
    for i in range(3):
        keyboard.add(InlineKeyboardButton(text=board[i][0], callback_data=f'{prefix}_{i}_0'),
                     InlineKeyboardButton(text=board[i][1], callback_data=f'{prefix}_{i}_1'),
                     InlineKeyboardButton(text=board[i][2], callback_data=f'{prefix}_{i}_2'))
    if 'end' in prefix:
        keyboard.add(InlineKeyboardButton(text='Еще раз', callback_data='ttt'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='start'))
    return keyboard


def notifications(check):
    keyboard = InlineKeyboardMarkup()
    if check:
        keyboard.add(InlineKeyboardButton(text='Отписаться', callback_data='subscribe_off'))
    else:
        keyboard.add(InlineKeyboardButton(text='Подписаться', callback_data='subscribe_on'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='start'))
    return keyboard


def rand():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Монетка', callback_data='rand_coin'),
                 InlineKeyboardButton(text='Кубик', callback_data='rand_dice'))
    keyboard.add(InlineKeyboardButton(text='Случайное число от 1 до 100', callback_data='rand_number'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='start'))
    return keyboard


def games():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Кости', callback_data='games_dice'),
                 InlineKeyboardButton(text='Казино', callback_data='games_casino'))
    keyboard.add(InlineKeyboardButton(text='Дартс', callback_data='games_darts'),
                 InlineKeyboardButton(text='Боулинг', callback_data='games_bowling'))
    keyboard.add(InlineKeyboardButton(text='Баскетбол', callback_data='games_basketball'),
                 InlineKeyboardButton(text='Футбол', callback_data='games_football'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='start'))
    return keyboard


def back(text=locales.back, category='start'):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text=text, callback_data=category))
    return keyboard
