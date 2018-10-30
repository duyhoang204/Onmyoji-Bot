import time

import screen_processor, emu_manager

# Souls check!
def soul_change(shiki_img, soulset_img=None):
    screen_processor.abs_search("bottom_scroll.png", click=True)
    screen_processor.wait("shiki_icon.png", click=True)
    screen_processor.wait("tho.png")
    screen_processor.wait(shiki_img, click=True)
    # Click on soul set
    emu_manager.mouse_click(553, 187)

    screen_processor.wait("soul_change.png", click=True)
    screen_processor.wait("soul_save.png")
    if soulset_img and screen_processor.abs_search(soulset_img)[0] == -1:
        #TODO un-hardcode this
        emu_manager.mouse_click(568, 205, sleep=1)
        emu_manager.mouse_click(745, 458)
        screen_processor.wait(soulset_img)
    else:
        emu_manager.mouse_click(568, 205, sleep=1)
        emu_manager.mouse_click(745, 458)
        time.sleep(2)
    # Back
    emu_manager.mouse_click(49, 31, sleep=0.5)
    emu_manager.mouse_click(49, 31, sleep=0.5)
    emu_manager.mouse_click(49, 31, sleep=0.5)

def onmyoji_change():
    pass