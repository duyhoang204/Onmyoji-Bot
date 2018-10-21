import random
import time

import cv2
import logging

import emu_manager
import screen_processor

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s'
                    # filename='logs/main.log',
                    # filemode='w+')
                    )

logger = logging.getLogger('')


def click_image(image, pos, offset_width=0, offset_height=0, sleep=0.5):
    path = screen_processor.get_image_path(image)
    img = cv2.imread(path)
    height, width, channels = img.shape
    emu_manager.mouse_click(pos[0] + width / 2 + offset_width, pos[1] + height / 2 + offset_height)
    time.sleep(sleep)


def find_and_click(img_name, region, double_click=True):
    pos = screen_processor.abs_search(img_name, region)
    if pos[0] != -1:
        click_image(img_name, pos)
        return True

    return False

def r(num, rand):
    return num + rand*random.random()

def get_logger():
    return logger