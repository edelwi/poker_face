from logging.handlers import RotatingFileHandler
import time

from PIL import Image, UnidentifiedImageError
import face_recognition
import os
from shutil import copyfile

import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/poker_face.log',
                                   maxBytes=1024000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
log.addHandler(file_handler)


class FaceNotFound(Exception):
    """ FaceNotFound exception class.

       Args:
           value (str): Description of the exception.

       """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


def create_dir(full_dir_path):
    if not os.path.exists(full_dir_path):
        os.makedirs(full_dir_path)


def get_avatars(image, top, right, bottom, left):
    height, width, c = image.shape

    f_height = bottom - top
    f_width = right - left

    top_shift = int(f_height // 1.5)
    bottom_shift = int(f_height // 1.5)

    left_shift = f_width // 2
    right_shift = f_width // 2

    new_top = top - top_shift if top - top_shift >= 0 else 0
    # delta_top = - top - top_shift if top - top_shift < 0 else 0
    # if delta_top: print(f'^^ {delta_top}')

    new_bottom = bottom + bottom_shift if bottom + bottom_shift <= height else height
    # delta_bottom = width - bottom + bottom_shift if bottom + bottom_shift > width else 0
    # if delta_bottom: print(f'vv {delta_bottom}')

    new_left = left - left_shift if left - left_shift >= 0 else 0
    # delta_left = -left - left_shift if left - left_shift < 0 else 0
    # if delta_left: print(f'<< {delta_left}')

    new_right = right + right_shift if right + right_shift <= width else width
    # delta_right = width - right + right_shift if right + right_shift > width else 0
    # if delta_right: print(f'>> {delta_right}')

    face_image = image[new_top:new_bottom, new_left:new_right]
    pil_image = Image.fromarray(face_image)
    # print(f'{width =}, {height =}')
    # print(f'{top =}, {right =}, {bottom =}, {left =} ==> {new_top =}, {new_right =}, {new_bottom =}, {new_left =}')
    return pil_image


def get_faces(file_name):

    try:
        image = face_recognition.load_image_file(file_name)
    except UnidentifiedImageError as e:
        log.warning(f'Error: {e}')
        raise
    face_locations = face_recognition.face_locations(image)
    if len(face_locations) == 0:
        log.warning(f'Can not find face in {file_name}')
        raise FaceNotFound(f'Can not find face in {file_name}')
    elif len(face_locations) >= 1:
        faces = []
        for n, face_location in enumerate(face_locations):
            faces.append(get_avatars(image, *face_location))
        return faces
    else:
        log.warning(f'What is it {file_name}')
        raise FaceNotFound(f'What is it {file_name}')


def set_size(img, max_width=150, max_height=200):
    if img.size[0] == 0 or img.size[1] == 0:
        return
    elif img.size[0] <= max_width and img.size[1] <= max_height:
        return img
    height_rate = max_height / float(img.size[1])
    width_rate = max_width / float(img.size[0])
    rate = max(height_rate, width_rate)
    width_size = int(float(img.size[0]) * rate)
    height_size = int(float(img.size[1]) * rate)
    img_resized = img.resize((width_size, height_size))  # , PIL.Image.NEAREST
    return img_resized


def runner(resize=None):  # resize: {'max_width': 150, 'max_height': 200}
    t0 = time.time()
    base_dir = os.path.dirname(__file__)
    if os.path.isabs(IMG_DIR):
        pic_dir = IMG_DIR
    else:
        pic_dir = os.path.join(base_dir, IMG_DIR)
    i = 0
    f = 0
    s = 0

    base_dir = os.path.dirname(__file__)
    if os.path.isabs(FAIL_DIR):
        pic_fail = FAIL_DIR
    else:
        pic_fail = os.path.join(base_dir, FAIL_DIR)
    create_dir(pic_fail)

    if os.path.isabs(OUT_DIR):
        pic_out = OUT_DIR
    else:
        pic_out = os.path.join(base_dir, OUT_DIR)
    create_dir(pic_out)

    for img_file in os.listdir(pic_dir):
        img_file_full = os.path.join(pic_dir, img_file)
        file_name_base = os.path.basename(img_file)
        i += 1
        try:
            faces = get_faces(img_file_full)
        except UnidentifiedImageError as e:
            f += 1
            copyfile(img_file_full, os.path.join(pic_fail, file_name_base))
        except FaceNotFound as e:
            f += 1
            copyfile(img_file_full, os.path.join(pic_fail, file_name_base))
        else:
            for n, face in enumerate(faces):
                if resize:
                    if isinstance(resize, dict):
                        max_width = resize.get('max_width', 150)
                        max_height = resize.get('max_height', 200)
                        face = set_size(face, max_width, max_height)
                    else:
                        face = set_size(face)
                f_name, ext = os.path.splitext(file_name_base)
                new_name = os.path.join(pic_out, f'{f_name}_cut_{n}.png')
                face.save(new_name, format='PNG')
            s += 1
    t1 = time.time()
    log.info(f'Duration {t1-t0}, success: {s}, fail: {f}, total: {i}')


IMG_DIR = 'pic'
OUT_DIR = 'pic-out'
FAIL_DIR = 'pic-fail'

if __name__ == "__main__":
    runner(resize={'max_width': 250, 'max_height': 400})
