import datetime
import sqlite3


def check_user(userid, username):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    row = q.execute(f'SELECT * FROM users where id = {userid}').fetchone()
    if row is None:
        now_date = str(datetime.datetime.now())[:10]
        q.execute(
            f'INSERT INTO users (id,name,data_reg) VALUES ({userid}, "{username}", "{now_date}")')
    else:
        q.execute(f'UPDATE users SET name="{username}" WHERE id={userid}')
    connection.commit()


def users_weather_notifications(userid=None):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    users = q.execute('SELECT id FROM users WHERE weather_notifications="yes"').fetchall()
    if userid:
        return any(i[0] == userid for i in users)
    return tuple(map(lambda x: x[0], users)) if users else []


def subscribe_weather_notifications(userid, status='yes'):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute(f'UPDATE users SET weather_notifications="{status}" WHERE id={userid}')
    connection.commit()


def last_weather(userid):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    last = q.execute(f'SELECT last_weather FROM users WHERE id={userid}').fetchone()[0]
    return last


def last_weather_update(userid, place):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute(f'UPDATE users SET last_weather="{place}" WHERE id={userid}')
    connection.commit()
