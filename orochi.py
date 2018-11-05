from main import *
import shiki_utils

logger = util.get_logger()

class Orochi:
    def __init__(self):
        pass

    def start(self, restart=True):
        if restart:
            logger.info("Restarting game...")
            restart_game()
            go_to_main_screen()

        shiki_utils.soul_change("irabaki.png", "ira_soulset.png")

        # Wait for invitation
        logger.info("Waiting for party invitation...")
        while screen_processor.abs_search("party_orochi.png")[0] == -1:
            time.sleep(2)
        logger.info("Found party!")
        time.sleep(1)
        screen_processor.abs_search("party_check.png", click=True)
        logger.info("Joined party!")

        # Now wait for battle
        screen_processor.wait("realm_back_btn.png")

        logger.info("Got into battle!")
        emu_manager.mouse_click(*BATTLE_START_BTN)

        battle_count = 0
        battle_start = time.time()
        while True:
            screen_processor.wait("auto_icon.png", precision=0.95)
            while screen_processor.abs_search("auto_icon.png")[0] != -1:
                time.sleep(1)

            battle_count += 1
            battle_end = time.time()
            quit_party = False
            while screen_processor.abs_search("shiki_icon.png",
                                              (1090, 600, WINDOW_WIDTH, WINDOW_HEIGHT),
                                              precision=0.9)[0] == -1:
                emu_manager.mouse_click(953, 570)

            while screen_processor.abs_search("realm_back_btn.png", (0,0,100,100))[0] == -1:
                if screen_processor.abs_search("party_invite_btn.png", PARTY_SLOT_2_REGION)[0] != -1:
                    quit_party = True
                    break

            if quit_party:
                # Host quit!
                logger.info("Host quit! Ending auto...")
                buff_off([1])
                duration = battle_end - battle_start
                hour = int(duration / (60 * 60))
                mins = int((duration - hour * 60 * 60) / 60)
                secs = int(duration % 60)
                logger.info("Time: {}h{}m{}s, Sushi: {}".format(hour, mins, secs, battle_count * 4))

                # Click quit
                time.sleep(1)
                emu_manager.mouse_click(235, 600, sleep=1)
                emu_manager.mouse_click(763, 430, sleep=1)
                break

    def kill_popups(self, run_time, start_time=time.time()):
        logger.info("Start hunting for in-game popup...")
        while not FINISHED_MAIN_LOOP[0]:
            if screen_processor.abs_search("wanted_4.png", WANTED_2_SEARCH_BOX)[0] != -1:
                # Deny wanted req
                logger.info("WANTED FOUND!")
                emu_manager.mouse_click(*WANTED_CANCEL)
            if screen_processor.abs_search("party_gear.png", click=True)[0] != -1:
                # Auto join party
                logger.info("Auto joining party...!")
            time.sleep(1)
        logger.info("End hunting for in-game popup.")

import sys
if __name__ == "__main__":
    restart = int(sys.argv[1])
    from concurrent.futures import ThreadPoolExecutor, as_completed
    start_time = time.time()
    run_time = bot_cfg.get_run_time_in_seconds()
    hwnd = set_up()

    orochi = Orochi()
    logger.info("Starting demon encounter bot...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(orochi.start, restart),
                   executor.submit(orochi.kill_popups, run_time, start_time=start_time)}

        for f in as_completed(futures):
            rs = f.result()
