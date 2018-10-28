import random

from main import *

logger = util.get_logger()


class Better:
    def __init__(self):
        pass

    def start(self):
        if not is_in_town():
            logger.info("Restarting game...")
            restart_game()
            go_to_town()
            time.sleep(5)
        # Click on bet dude
        emu_manager.mouse_click(*BET_DUDE)
        screen_processor.wait("bet_sign.png")

        if screen_processor.abs_search("bet_complete.png")[0] != -1:
            logger.info("Already bet this round!")
            FINISHED_MAIN_LOOP[0] = True
            return

        # Check previous bet
        if screen_processor.abs_search("bet_win.png")[0] != -1:
            logger.info("We won! Yay!")
            # Claim reward
            emu_manager.mouse_click(*BET_CLAIM_REWARD)
            time.sleep(10)
            # Click again to stop animation
            emu_manager.mouse_click(*BET_CLAIM_REWARD)
            time.sleep(1)

        screen_processor.abs_search("next_bet.png", click=True)
        logger.info("Proceeding to next bet...")
        time.sleep(2)

        def pick_side(tries=0):
            # Try picking a side with more people first
            try:
                red = int(screen_processor.get_text(290, 604, 408, 654))
                logger.info("Red: {}".format(red))
                blue = int(screen_processor.get_text(931, 604, 1022, 654))
                logger.info("Blue: {}".format(blue))
                rate = float(red/(blue+red))
                logger.info("Win rate for red: {}".format(rate))
                if rate >= 0.7:
                    return 0
                elif rate <= 0.3:
                    return 1
                else:
                    logger.info("Randomizing choices...")
                    return 0 if random.randint(1, 100) <= 50 else 1
            except:
                if tries < 10:
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
            side = 0 if random.randint(1, 100) <= 50 else 1

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

        emu_manager.mouse_click(*BET_CLICK_OUT, sleep=1)
        # Confirm
        emu_manager.mouse_click(*BET_CONFIRM, sleep=1)
        logger.info("Bet done!")
        # Close bet panel
        emu_manager.mouse_click(1147, 169)
        FINISHED_MAIN_LOOP[0] = True


if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor, as_completed
    start_time = time.time()
    run_time = bot_cfg.get_run_time_in_seconds()
    hwnd = set_up()

    logger.info("Starting bet bot...")
    # Better().start()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(Better().start),
                   executor.submit(kill_popups, run_time, start_time=start_time)}

        for f in as_completed(futures):
            rs = f.result()
