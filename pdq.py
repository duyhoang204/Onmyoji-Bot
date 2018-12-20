from base_task import BaseTask
from main import *

logger = util.get_logger()


class PDQ(BaseTask):
    def __init__(self):
        super(BaseTask, self).__init__()

    def start(self, restart=False):
        if restart:
            logger.info("Restarting game...")
            restart_game()
            go_to_main_screen()
            time.sleep(5)

        # emu_manager.mouse_drag(200, 400, 1200, 400, duration=2000)
        time.sleep(2)
        # Wait for invitation
        logger.info("Waiting for pdq activation...")
        begin = time.time()
        while screen_processor.abs_search("pdq_invite.png", click=True)[0] == -1:
            time.sleep(1)
            if time.time() - begin > 30 * 60:
                logger.info("No one invited me :( Finished pdq")
                FINISHED_MAIN_LOOP[0] = True
                return

        begin = time.time()
        screen_processor.abs_search("bottom_scroll.png", (1000, 550, WINDOW_WIDTH, WINDOW_HEIGHT), precision=0.9, click=True)
        # Click on Guild icon in main screen
        emu_manager.mouse_click(408, 628)
        screen_processor.wait("pdq_icon.png", precision=0.9, click=True)
        screen_processor.wait("pdq_target_guild.png", precision=0.94, click=True)
        screen_processor.wait("pdq_enemy_house.png")
        logger.info("Got to PDQ main screen")

        while screen_processor.abs_search("pdq_battle_lb_icon.png", precision=0.94)[0] == -1:
            # Click Fight!
            emu_manager.mouse_click(WINDOW_WIDTH - 100, WINDOW_HEIGHT - 100)
            time.sleep(2)
        logger.info("Started battle phase")
        # We got into battle!
        screen_processor.wait("realm_back_btn.png")
        select_team(1)
        time.sleep(1)
        emu_manager.mouse_click(*BATTLE_START_BTN)
        # screen_processor.wait("auto_icon.png")
        # while screen_processor.abs_search("auto_icon.png")[0] != -1:
        #     time.sleep(2)

        won = 0
        while time.time() - begin < 30 * 60:
            if screen_processor.abs_search("pdq_complete.png", precision=0.93)[0] != -1:
                break
            # if screen_processor.abs_search("pdq_enemy_house.png")[0] != -1:
            #     logger.info("We lost :(")
            #     break
            # if screen_processor.abs_search("battle_reward.png")[0] != -1:
            #     won += 1
            #     logger.info("Win: {}".format(won))
            #     screen_processor.wait_disappear("battle_reward.png", click=True)
            #     time.sleep(2)
            #     if screen_processor.abs_search("pdq_complete.png", precision=0.93)[0] != -1:
            #         break
            #
            #     # Keep battling
            #     emu_manager.mouse_click(*BATTLE_START_BTN)
            #     screen_processor.wait("auto_icon.png")
            #     while screen_processor.abs_search("auto_icon.png")[0] != -1:
            #         time.sleep(2)
            emu_manager.mouse_click(*PDQ_TARGET)
            time.sleep(2)

        logger.info("Finished pdq!")
        FINISHED_MAIN_LOOP[0] = True


import sys
if __name__ == "__main__":
    do_restart = int(sys.argv[1])
    from concurrent.futures import ThreadPoolExecutor, as_completed
    start_time = time.time()
    run_time = bot_cfg.get_run_time_in_seconds()
    hwnd = set_up()

    pdq = PDQ()
    logger.info("Starting pdq bot...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(pdq.start, do_restart),
                   executor.submit(pdq.kill_popups, run_time, start_time=start_time)}

        for f in as_completed(futures):
            rs = f.result()
