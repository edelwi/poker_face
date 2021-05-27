from logging.handlers import RotatingFileHandler
import time
from PIL import Image, UnidentifiedImageError
import face_recognition
import os
from shutil import copyfile

import logging
logging.basicConfig()
log = logging.getLogger()
#log.setLevel(logging.INFO)
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/poker_face.log',
                                   maxBytes=1024000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.DEBUG)
log.addHandler(file_handler)

def get_avatar(image, top, right, bottom, left):
    height, width, c = image.shape

    f_height = bottom - top
    f_width = right - left

    top_shift = int(f_height // 1.7)
    bottom_shift = f_height // 2

    left_shift = f_width // 2
    right_shift = f_width // 2

    new_top = top - top_shift if top - top_shift >= 0 else 0
    delta_top = - top - top_shift if top - top_shift < 0 else 0
    if delta_top: print(f'^^ {delta_top}')

    new_bottom = bottom + bottom_shift if bottom + bottom_shift <= height else height
    delta_bottom = width - bottom + bottom_shift if bottom + bottom_shift > width else 0
    if delta_bottom: print(f'vv {delta_bottom}')

    new_left = left - left_shift if left - left_shift >= 0 else 0
    delta_left = -left - left_shift if left - left_shift < 0 else 0
    if delta_left: print(f'<< {delta_left}')

    new_right = right + right_shift if right + right_shift <= width else width
    delta_right = width - right + right_shift if right + right_shift > width else 0
    if delta_right: print(f'>> {delta_right}')

    face_image = image[new_top:new_bottom, new_left:new_right]
    pil_image = Image.fromarray(face_image)
    print(f'{width =}, {height =}')
    print(f'{top =}, {right =}, {bottom =}, {left =} ==> {new_top =}, {new_right =}, {new_bottom =}, {new_left =}')
    return pil_image


def get_face(file_name):
    file_name_base = os.path.basename(file_name)
    base_dir = os.path.dirname(__file__)
    pic_fail = os.path.join(base_dir, 'pic-fail2')
    try:
        image = face_recognition.load_image_file(file_name)
    except UnidentifiedImageError as e:
        log.warn(f'Error: {e}')
        copyfile(file_name, os.path.join(pic_fail, file_name_base))
        return False
    face_locations = face_recognition.face_locations(image)
    if len(face_locations) == 0:
        log.warning(f'Can not find face in {file_name}')
        copyfile(file_name, os.path.join(pic_fail, file_name_base))
        return False
    elif len(face_locations) > 1:
        log.warning(f'Too many faces ({len(face_locations)}) in {file_name}')
        copyfile(file_name, os.path.join(pic_fail, file_name_base))
        return False
    elif len(face_locations) == 1:
        face_location = face_locations[0]
        # top, right, bottom, left = face_location

        new_image = get_avatar(image, *face_location)

        pic_out = os.path.join(base_dir, 'pic-out2')
        if not os.path.exists(pic_out):
            os.mkdir(pic_out)
        f_name, ext = os.path.splitext(file_name_base)
        new_name = os.path.join(pic_out, f'{f_name}_cut{ext}')
        new_image.save(new_name, format='PNG')
        return True
    else:
        log.warning(f'What is it {file_name}')
        copyfile(file_name, os.path.join(pic_fail, file_name_base))
        return False


def runner():
    t0 = time.time()
    base_dir = os.path.dirname(__file__)
    pic_dir = os.path.join(base_dir, 'pic')
    i = 0
    f = 0
    s = 0
    for img in os.listdir(pic_dir):
        if img.endswith(".JPG"):
            i += 1
            if get_face(os.path.join(pic_dir, img)):
                print(f'{os.path.basename(os.path.join(pic_dir, img))} - OK')
                s += 1
            else:
                print(f'{os.path.basename(os.path.join(pic_dir, img))} - Fail!')
                f += 1
    t1 = time.time()
    print(f'Duration {t1-t0}, success: {s}, fail: {f}, total: {i}')


if __name__ == "__main__":
    runner()