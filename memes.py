import random
import vk
import config

memes = vk.get_photo_links(config.cb_id)
cats = vk.get_photo_links(config.cats_id)


def vk_group_photo(links):
    return links[random.randint(0, 999)]


def update_links(group_id):
    return vk.get_photo_links(group_id)
