from aiogram import types

admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
admin.row('Статистика', 'Рассылка')
admin.row('Настройки', 'Пользователи')
admin.row('Арбитражи', 'Cделки')

main = types.ReplyKeyboardMarkup(resize_keyboard=True)
main.row('Погода', 'Мем', 'Котик')
main.row('крестики', 'нолики', 'крестики-нолики')
main.row('Космос', '🔔', 'кости', 'казино')
main.row('Отдаю свою судьбу в чужие руки')
main.row('Связь с администрацией')


def back(text='Назад', category='start'):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=text, callback_data=category))
    return keyboard
