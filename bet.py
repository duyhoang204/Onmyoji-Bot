import time
import random

import logging

import emu_manager
import screen_processor
import util
from common import *
from main import set_up, kill_popups, FINISHED_MAIN_LOOP

logger = util.get_logger()

class Better:
    def __init__(self):
        pass

    def start(self):
        logger.info("Starting...")

        if screen_processor.abs_search("bet_complete.png")[0] != -1:
            logger.info("Already bet this round!")
            FINISHED_MAIN_LOOP[0] = True
            return

        # Check previous bet
        if screen_processor.abs_search("bet_win.png")[0] != -1:
            logger.info("We won! Yay!")
            #Claim reward
            emu_manager.mouse_click(*BET_CLAIM_REWARD)
            time.sleep(10)
            # Click again to stop animation
            emu_manager.mouse_click(*BET_CLAIM_REWARD)
            time.sleep(1)

        screen_processor.abs_search("next_bet.png", click=True)
        logger.info("Proceeding to next bet...")

        def pick_side(tries=0):
            # Try picking a side with more people first
            print(tries)
            try:
                red = int(screen_processor.get_text(290, 604, 408, 654))
                logger.info("Red: {}".format(red))
                blue = int(screen_processor.get_text(931, 604, 1022, 654))
                logger.info("Blue: {}".format(blue))
                return 0 if red - blue > 0 else 1
            except:
                if tries < 5:
                    # Exit then enter again
                    emu_manager.mouse_click(1148, 169, sleep=1)
                    emu_manager.mouse_click(713, 421, sleep=5)
                    tries += 1
                    return pick_side(tries)
                else:
                    raise

        try:
            side = pick_side()
        except:
            logger.info("Could not decide which side is better, trying picking randomly...")
            # Randomly pick side
            side = random.randint(0,1)

        logger.info("Picked {}!".format("blue" if side else "red"))

        time.sleep(2)
        emu_manager.mouse_click(*BET_SIDES[side], sleep=2)
        # Select reward
        extra = screen_processor.abs_search("bet_extra.png")
        if extra[0] != -1:
            # Extra bet!
            emu_manager.mouse_click(extra[0]+70, extra[1]+70, sleep=1)
        else:
            # Go with 200k
            emu_manager.mouse_click(*BET_200K, sleep=1)

        emu_manager.mouse_click(*BET_CLICK_OUT)
        # Confirm
        emu_manager.mouse_click(*BET_CONFIRM)
        logger.info("Bet done!")
        FINISHED_MAIN_LOOP[0] = True

if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor, as_completed
    start_time = time.time()
    run_time = 60*3
    hwnd = set_up()

    logger.info("Starting bot...")
    # Better().start()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(Better().start),
                   executor.submit(kill_popups, run_time, start_time=start_time)}

        for f in as_completed(futures):
            rs = f.result()