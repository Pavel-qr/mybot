from aiogram import executor

from bot import on_startup, dp, bot
# from handlers_admin import register_admin, register_inline_handlers
# from handlers_user import register_user, register_last
from handlers_admin import dp
from handlers_user import dp


# register_user(dp)
# register_admin(dp)
# register_inline_handlers(dp)
# register_last(dp)


async def test(_):
    a = await bot.get_me()
    print(a)


executor.start_polling(dp, skip_updates=True, on_startup=[on_startup, test])
