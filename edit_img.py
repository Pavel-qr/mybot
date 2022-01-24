import io
from random import randint
from PIL import Image


def image_to_byte_array(image: Image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


def crop_img(img, coords=None):
    img = Image.open(img)
    print(img.size)
    img = img.crop(coords)
    return image_to_byte_array(img)


def crop_random(img, percent=10):
    img = Image.open(img)
    x = randint(0, int(img.size[0]/100*(100-percent)))
    y = randint(0, int(img.size[1]/100*(100-percent)))
    box = (x, y, int(x+img.size[0]/100*percent), int(y+img.size[1]/100*percent))
    img = img.crop(box)
    return image_to_byte_array(img)


if __name__ == '__main__':
    for i in range(1, 7):
        img = Image.open(f'img/{i}.png')
        print(img.size)
    # coin_edge.resize((926, 928)).save('img/coin_edge.png')
