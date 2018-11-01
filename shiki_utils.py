import time

import screen_processor, emu_manager

# Souls check!
def soul_change(shiki_img, soulset_img):
    screen_processor.abs_search("bottom_scroll.png", precision=0.9, click=True)
    screen_processor.wait("shiki_icon.png", precision=0.9, click=True)
    screen_processor.wait("tho.png")
    screen_processor.wait(shiki_img, click=True)
    # Click on soul set
    emu_manager.mouse_click(553, 187)

    screen_processor.wait("soul_change.png", click=True)
    screen_processor.wait("soul_save.png")
    # time.sleep(1)
    soulset_pos = screen_processor.abs_search(soulset_img, precision=0.95)
    if soulset_pos[0] != -1:
        w, h = screen_processor.get_image_res(soulset_img)
        emu_manager.mouse_click(soulset_pos[0]+w-30, soulset_pos[1]+h-60, sleep=1)
        screen_processor.wait("confirm_soul_btn.png", click=True, sleep=0.2)
        screen_processor.wait_disappear(soulset_img, precision=0.95)
        time.sleep(0.7)

    # Back
    emu_manager.mouse_click(49, 31, sleep=1)
    emu_manager.mouse_click(49, 31, sleep=1)
    emu_manager.mouse_click(49, 31, sleep=1)

def onmyoji_change():
    pass