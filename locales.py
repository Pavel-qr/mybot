import config

only_private = 'Всем привет! Наш бот не работает в чатах\n' \
               f'Пишите напрямую - @{config.bot_user_name}'

error_message = 'Неизвестная ошибка. Пожалуйста, обратитесь к админу, для скорейшего исправления'
admin_message = 'Привет, админ'
select_user = 'Выбери пользователя:'
write = 'Написать'
pays = 'Оплаты'
write_answer = 'Ответ пиши'
void = ''

statistic_text = 'Пользователей: {users_count}\n' \
                 'Папок: {folders_count}\n' \
                 'Файлов: {files_count}\n'
date_format = '%A %d %B'
short_date_format = '%d %B'
time_format = '%d %B'

# welcome
start_message = 'Привет!'

menu_message = 'Привет!'

unknown_message = 'Когда-нибудь я скажу тебе всё, что думаю...\n\n\n' \
                  'А пока используй кнопки'

beauty_message = 'Красиво. Я тоже так хочу😯'

# help
# admin_link = 'Контакт админа'
# help_text = f'{config.bot_name}\n\n' \
#             '<b> - Как работает?</b>\n' \
#             '<b> - Контакт админа</b>\n' \
#             'Пожалуйста, пишите админу только в том случае, если не нашли решения самостоятельно\n\n' \
#             f'Написать можно напрямую - @{config.admin_name}\n' \
#             'Или по кнопке ниже'

# buttons
weather_button = 'Погода'
folder_button = 'Папка'
space_button = 'Космос'
mem_button = 'Мем'
cat_button = 'Котик'
ttt_button = 'Крестики-нолики'
game_button = 'Игры'
notification_button = 'Уведомления'
fate_button = 'Отдаю свою судьбу в чужие руки'
admin_button = 'Связь с администрацией'

statistic_button = 'Статистика'
mail_button = 'Рассылка'
vk_button = 'вк'
users_button = 'Пользователи'

start_command = 'Привет!'
help_command = 'Помощь'
settings_command = 'Настройки'
weather_command = 'Погода'
folder_command = 'Открыть папку'

back = 'Назад'

weather = '{city} {time}\n' \
          'На улице {status}, {temperature}°C\n' \
          'Ощущается как {feels_like}°C\n' \
          '💦 Влажность — {humidity}%\n' \
          '💨 Ветер — {wind} м/с\n\n' \
          '🌅 Рассвет в {sunrise_time}\n' \
          '🌆 Закат в {sunset_time}'
