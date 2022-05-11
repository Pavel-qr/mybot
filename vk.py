import datetime
import asyncio
import vk_api
import config


def auth(token=config.vk_token):
    """ Пример отображения 5 последних альбомов пользователя """
    vk_session = vk_api.VkApi(token=token)
    try:
        return vk_session.get_api()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return


def get_photo_links(group_id):
    vk_session = auth()
    if not vk_session:
        return
    photos = vk_session.photos.get(owner_id=group_id, album_id='wall', rev=1, count=1000)
    urls = [i['sizes'][-1]['url'] for i in photos['items']]
    return urls


async def get_status(get_vk_id, cond, param):
    current_status = True
    vk_session = auth()
    if not vk_session:
        return
    profile = vk_session.users.get(user_id=get_vk_id, fields='online, last_seen')[0]
    yield f"{profile['first_name']} {profile['last_name']} {profile['online']}"
    while cond(param):
        await asyncio.sleep(1)
        profile = vk_session.users.get(user_id=get_vk_id, fields='online, last_seen')[0]
        if not current_status and profile['online']:  # если появился в сети, то выводим время
            now = datetime.datetime.now()
            yield f'{profile["first_name"]} {profile["last_name"]} Появился в сети в: {now.strftime("%d-%m-%Y %H:%M")}'
            current_status = True
        if current_status and not profile['online']:  # если был онлайн, но уже вышел, то выводим время выхода
            yield f"{profile['first_name']} {profile['last_name']} Вышел из сети: {datetime.datetime.fromtimestamp(profile['last_seen']['time']).strftime('%d-%m-%Y %H:%M')}"
            current_status = False


async def main():
    a = get_status(118145515, lambda x: x < 4, 3)
    async for i in a:
        print(i)
    print('ok')


if __name__ == '__main__':
    asyncio.run(main())
