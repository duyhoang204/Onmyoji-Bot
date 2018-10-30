from main import *

logger = util.get_logger()

class Orochi:
    def __init__(self):
        pass

    def start(self):
        logger.info("Restarting game...")
        # restart_game()

        # Souls check!
        screen_processor.abs_search("shiki_icon.png", click=True)
        screen_processor.wait("tho.png")
        screen_processor.abs_search("irabaki.png", click=True)
        # Click on soul set
        emu_manager.mouse_click(553, 187)

        screen_processor.wait("soul_change.png", click=True)
        screen_processor.wait("soul_save.png")
        if screen_processor.abs_search("ira_soulset.png")[0] == -1:
            #TODO un-hardcode this
            emu_manager.mouse_click(568, 205, sleep=1)
            emu_manager.mouse_click(745, 458)
            screen_processor.wait("ira_soulset.png")

        # Back
        emu_manager.mouse_click(49, 31, sleep=0.5)
        emu_manager.mouse_click(49, 31, sleep=0.5)
        emu_manager.mouse_click(49, 31, sleep=0.5)


        # Wait for invitation
        logger.info("Waiting for party invitation...")
        while screen_processor.abs_search("party_orochi.png")[0] == -1:
            time.sleep(2)
        logger.info("Found party!")
        time.sleep(2)
        screen_processor.abs_search("party_check.png", click=True)
        logger.info("Joined party!")

        # Now wait for battle
        screen_processor.wait("realm_back_btn.png")

        logger.info("Got into battle!")
        emu_manager.mouse_click(*BATTLE_START_BTN)

        #TODO hard coded time!
        st = time.time()
        while time.time() - st < 60 * 60 * 3:
            screen_processor.wait("auto_icon.png")
            while screen_processor.abs_search("auto_icon.png")[0] != -1:
                time.sleep(1)

            while screen_processor.abs_search("realm_back_btn.png", (0,0,71,94))[0] == -1:
                emu_manager.mouse_click(634, 547)

        FINISHED_MAIN_LOOP[0] = True

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

if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor, as_completed
    start_time = time.time()
    run_time = bot_cfg.get_run_time_in_seconds()
    hwnd = set_up()

    orochi = Orochi()
    logger.info("Starting demon encounter bot...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(orochi.start),
                   executor.submit(orochi.kill_popups, run_time, start_time=start_time)}

        for f in as_completed(futures):
            rs = f.result()