from typing import List
from aiogram import types
import datetime

from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy import INTEGER, BIGINT, VARCHAR, BOOLEAN
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.orm import Session as S
from sqlalchemy.ext.declarative import declarative_base

import config

# Create a (lazy) database engine
engine = create_engine(config.engine)
# engine = create_engine(config.engine, pool_size=100, max_overflow=50)

# Create a base class to define all the database subclasses
TableDeclarativeBase = declarative_base(bind=engine)

# Create a Session class able to initialize database sessions
Session = sessionmaker()


# Define all the database tables using the sqlalchemy declarative base
class User(TableDeclarativeBase):
    """A Telegram user who used the bot at least once."""

    # Telegram reg data
    user_id = Column(BIGINT, primary_key=True)
    username = Column(VARCHAR(255))
    first_name = Column(VARCHAR(255), nullable=False)
    reg_date = Column(VARCHAR(255))
    last_date = Column(VARCHAR(255))
    last_weather = Column(VARCHAR(255), default='Санкт-Петербург')
    weather_notifications = Column(BOOLEAN, default=True)
    status = Column(BOOLEAN, default=True)
    last_message = Column(VARCHAR(255))

    # Extra table parameters
    __tablename__ = "users"

    def __init__(self, telegram_user, **kwargs):
        # Initialize the super
        super().__init__(**kwargs)
        # Get the data from telegram
        self.user_id = telegram_user.id
        self.first_name = telegram_user.first_name
        self.username = telegram_user.username
        self.reg_date = str(datetime.datetime.now())[:10]

    def __str__(self):
        """Describe the user in the best way possible given the available data."""
        if self.username is not None:
            return f"@{self.username}"
        else:
            return self.first_name

    def identifiable_str(self):
        """Describe the user in the best way possible, ensuring a way back to the database record exists."""
        return f"user_{self.user_id}_({str(self)})"

    def mention(self):
        """Mention the user in the best way possible given the available data."""
        if self.username is not None:
            return f"@{self.username}"
        else:
            return f'<a href="tg://user?user_id={self.user_id}">{self}</a>'

    def account(self):
        """Mention the user in the best way possible given the available data."""
        text = f'<b>{self.mention()}</b>\n' \
               f'<b>user_id:</b> <code>{self.user_id}</code>\n' \
               f'<b>Погода в <code>{self.last_weather}</code></b>\n' \
               f'<b>Уведомления о погоде:</b> {self.weather_notifications}\n\n' \
               f'<b>Последнее сообщение:</b> <code>{self.last_message}</code>\n' \
               f'<b>Последняя активность:</b> <code>{self.last_date}</code>\n\n' \
               f'<b>Дата регистрации:</b> <code>{self.reg_date}</code>\n' \
               f'<b>Статус:</b> <code>{self.status}</code>'
        return text


class VkInfo(TableDeclarativeBase):
    user_id = Column(BIGINT, ForeignKey("users.user_id", ondelete='CASCADE'),
                     primary_key=True, nullable=False)
    memes_id = Column(BIGINT, default=-67580761)
    online_user_id = Column(BIGINT, default=0)

    user = relationship("User", backref=backref("vk_info"), passive_deletes=True)
    
    # Extra table parameters
    __tablename__ = "vk_info"


class File(TableDeclarativeBase):
    file_id = Column(INTEGER, primary_key=True)
    user_id = Column(BIGINT, ForeignKey("users.user_id", ondelete='CASCADE'),
                     nullable=False)
    tg_id = Column(VARCHAR(255))
    file_type = Column(VARCHAR(255))

    user = relationship("User", backref=backref("files"), passive_deletes=True)

    # Extra table parameters
    __tablename__ = "files"


def check_user(message: types.Message):
    session: S = Session()
    user: User = session.query(User).filter_by(user_id=message.from_user.id).one_or_none()
    if not user:
        user = User(message.from_user)
        session.add(user)
    else:
        user.username = message.from_user.username
        user.last_message = message.text
        user.last_date = str(datetime.datetime.now())[:10]
    session.commit()
    return str(user)


def add_file(user_id, tg_id, file_type):
    session: S = Session()
    file = File(user_id=user_id, tg_id=tg_id, file_type=file_type)
    session.add(file)
    session.commit()


def delete_file(file_id):
    session: S = Session()
    session.query(File).filter_by(file_id=file_id).delete()
    session.commit()


def view_files(user_id):
    session: S = Session()
    files: List[File] = session.query(File).filter_by(user_id=user_id).all()
    return files


def check_vk(user_id, session: S = Session()):
    vk: VkInfo = session.query(VkInfo).filter_by(user_id=user_id).one_or_none()
    if vk is None:
        vk = VkInfo(user_id=user_id)
        session.add(vk)
        session.commit()


def last_weather(user_id):
    session: S = Session()
    last = session.query(User.last_weather).filter_by(user_id=user_id).one_or_none()
    return last[0]


def last_weather_update(user_id, place):
    session: S = Session()
    user: User = session.query(User).filter_by(user_id=user_id).one_or_none()
    user.last_weather = place
    session.commit()


def subscribe_weather_notifications(user_id):
    session: S = Session()
    user: User = session.query(User).filter_by(user_id=user_id).one_or_none()
    user.weather_notifications = not user.weather_notifications
    session.commit()


def users_weather_notifications():
    session: S = Session()
    users = session.query(User.user_id, User.last_weather).filter_by(weather_notifications=True).all()
    return users


def check_weather_notifications(user_id):
    return Session().query(User.weather_notifications).filter_by(user_id=user_id).one()[0]


def memes_id(user_id):
    session: S = Session()
    check_vk(user_id, session)
    meme_id = session.query(VkInfo.memes_id).filter_by(user_id=user_id).one_or_none()
    return meme_id


def vk_user_id(user_id):
    session: S = Session()
    check_vk(user_id, session)
    online_user_id = session.query(VkInfo.online_user_id).filter_by(user_id=user_id).one_or_none()
    return online_user_id


def change_vk(user_id, id_type, vk_user_id):
    session: S = Session()
    check_vk(user_id, session)
    session.query(VkInfo).filter_by(user_id=user_id).update({id_type: vk_user_id})
    session.commit()


def all_users(user_id=None):
    session: S = Session()
    if user_id:
        user: User = session.query(User).filter_by(user_id=user_id).one_or_none()
        return user
    users: List[User] = session.query(User).all()
    return users


TableDeclarativeBase.metadata.create_all()
