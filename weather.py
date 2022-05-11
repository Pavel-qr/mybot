from pprint import pprint
import time
from aiogram import types

from pyowm import OWM
from pyowm.commons import exceptions
from pyowm.utils.config import get_default_config

import config
import locales

config_dict = get_default_config()
config_dict['language'] = 'ru'
owm = OWM(config.owm_token, config_dict)
mgr = owm.weather_manager()


def current_weather(place):
    try:
        w = mgr.weather_at_place(place)
        # pprint(w.to_dict())
        er = ''
    except exceptions.NotFoundError:
        er = 'Это не страна и не город\n' \
             'Покажу тебе погоду в Санкт-Петербурге\n\n'
        w = mgr.weather_at_place('санкт-петербург, россия')
    city = w.location.name
    weather = w.weather
    temperature = weather.temperature('celsius')
    answer = er + locales.weather.format(
        status=weather.detailed_status, temperature=round(temperature.get('temp'), 1),
        feels_like=round(temperature.get('feels_like'), 1),
        humidity=weather.humidity, wind=weather.wind().get('speed'),
        sunrise_time=time.strptime(weather.sunrise_time(), locales.time_format),
        sunset_time=time.strptime(weather.sunset_time(), locales.time_format),
        city=city,
        time=time.strftime("%x %X", time.localtime())
    )
    return answer


def weather_at_location(location: types.Location):
    try:
        w = mgr.weather_at_coords(location.latitude, location.longitude)
        w = w.weather
        temperature = w.temperature('celsius')
        answer = f'Сейчас {time.strftime("%x %X", time.localtime())}\n' \
                 f'На улице {w.detailed_status}, {round(temperature["temp"])}°C\n' \
                 f'Ощущается как {round(temperature["feels_like"])}°C'
    except Exception:
        answer = 'Ошибка'
    return answer


if __name__ == '__main__':
    print(current_weather('Санкт-Петербург'))
