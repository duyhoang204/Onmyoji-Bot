import os
import time

import cv2
import numpy as np
from PIL import Image

# load the example image and convert it to grayscale
import pytesseract
import util
from bot_config import BotConfig
from common import WINDOW_WIDTH, WINDOW_HEIGHT
from imagesearch import region_grabber, imagesearcharea, imagesearcharea_v2, region_grabber_v2, image_search_multiple
from util import click_image


class ImageNotFoundException(Exception):
    pass

IMAGE_FOLDER = BotConfig().get_property("General", "image_folder")

logger = util.get_logger()
# TODO test
import emu_manager

hwnd = emu_manager.get_instance(int(BotConfig().get_property("Emulator", "use_device")))


def find_text(text, x1, y1, x2, y2):
    return text in get_text(x1, y1, x2, y2)


def get_text(x1, y1, x2, y2):
    import emu_manager
    hwnd = emu_manager.get_instance(int(BotConfig().get_property("Emulator", "use_device")))
    image = region_grabber_v2((x1, y1, x2, y2), hwnd)
    # image.save('testarea.png')  # useful for debugging purposes, this will save the captured region as "testarea.png"
    image = np.array(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # check to see if we should apply thresholding to preprocess the
    # image
    # if args["preprocess"] == "thresh":
    # gray = cv2.threshold(gray, 0, 255,
    #                          cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # make a check to see if median blurring should be done to remove
    # noise
    # elif args["preprocess"] == "blur":
    # gray = cv2.medianBlur(gray, 3)

    # write the grayscale image to disk as a temporary file so we can
    # apply OCR to it
    filename = "temp.png"
    cv2.imwrite(filename, gray)

    # load the image as a PIL/Pillow image, apply OCR, and then delete
    # the temporary file
    Image.open(filename)
    result = pytesseract.image_to_string(Image.open(filename))
    os.remove(filename)
    logger.info("Text on screen: \"{}\"".format(result))
    return result


def abs_search(file_name, pos_box=None, precision=0.8, get_absolute_pos=True, click=False):
    if not pos_box:
        pos_box = (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    path = get_image_path(file_name)

    # TODO refactor this

    result = imagesearcharea_v2(path, pos_box[0], pos_box[1], pos_box[2], pos_box[3], precision=precision, hwnd=hwnd)
    if get_absolute_pos and result[0] != -1:

        # Get and return absolute position of the image
        abs_result = (result[0]+pos_box[0], result[1]+pos_box[1])
        # abs_result = (result[0], result[1])
        if click:
            click_image(file_name, abs_result)
        logger.info("Found {} at {}".format(file_name, abs_result))
        return abs_result

    return result


def abs_search_multi(file_name, pos_box=None, precision=0.99):
    if not pos_box:
        pos_box = (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    path = get_image_path(file_name)

    result = image_search_multiple(path, pos_box[0], pos_box[1], pos_box[2], pos_box[3], precision=precision, hwnd=hwnd)
    logger.info("Found {} occurrence(s) of {}!".format(len(result), file_name))
    return [(x[0]+pos_box[0], x[1]+pos_box[1]) for x in result]


def wait(img, area=None, click=False, sleep=0.7, wait_count=100, click_offset=(0,0), pre_sleep=0, precision=0.8):
    for i in range(0, wait_count):
        pos = abs_search(img, area, precision=precision)
        if pos[0] != -1:
            logger.info("wait(): found {}!".format(img))
            if click:
                if pre_sleep:
                    time.sleep(pre_sleep)
                offset_width, offset_height = click_offset
                click_image(img, pos, offset_width=offset_width, offset_height=offset_height, sleep=0)
            return pos
        time.sleep(sleep)

    # Image not found
    raise ImageNotFoundException("Could not find {} on screen!".format(img))


def wait_disappear(img, area=None, sleep=0.7, wait_count=100, precision=0.9, click=False):
    for i in range(0, wait_count):
        pos = abs_search(img, area, precision=precision, click=click)
        if pos[0] != -1:
            time.sleep(sleep)
        else:
            return

    raise ImageNotFoundException("Image {} still on screen!".format(img))


def get_image_res(file_name):
    path = get_image_path(file_name)

    img = cv2.imread(path)
    height, width, channels = img.shape

    return width, height

def get_image_path(filename):
    return "{}/{}".format(IMAGE_FOLDER, filename)