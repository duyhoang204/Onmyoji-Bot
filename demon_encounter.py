import shiki_utils
from base_task import BaseTask
from main import *

logger = util.get_logger()


class DemonEncounter(BaseTask):
    def __init__(self):
        super(BaseTask, self).__init__()
        pass

    def start(self, restart=False):
        if restart:
            logger.info("Restarting game...")
            restart_game()
            go_to_main_screen()
            time.sleep(5)

        # shiki_utils.soul_change("shuten.png", "nura_soulset.png")

        count = 0
        while not self.join_boss_fight():
            # Close popup
            emu_manager.mouse_click(1132, 86)
            count += 1
            if count > 5:
                logger.info("We're out of luck this time, b-bye :(")
                return

        logger.info("Joined boss successfully!")
        # Now that we joined boss fight, just spamming the start button
        while screen_processor.abs_search("auto_icon.png")[0] == -1:
            emu_manager.mouse_click(*BATTLE_START_BTN)
            time.sleep(5)

        logger.info("Boss fight started!")
        while screen_processor.abs_search("de_boss_lb.png")[0] == -1:
            decoy = screen_processor.abs_search("decoy_debuff.png", (600, 350, 800, 500))
            if decoy[0] != -1:
                emu_manager.mouse_click(decoy[0]+20, decoy[1]+30)
            time.sleep(1)

        logger.info("Boss fight ended!")

        # Back out
        emu_manager.mouse_click(43, 43, sleep=1.5)
        emu_manager.mouse_click(746, 424)

        logger.info("Ended automation")
        FINISHED_MAIN_LOOP[0] = True

    def join_boss_fight(self):
        # Open chat
        while screen_processor.abs_search("sidebar_chat.png", SIDEBAR_BOX, precision=0.85)[0] == -1:
            emu_manager.mouse_click(*MESSAGE_ICON_MAIN, sleep=1.5)
            emu_manager.mouse_click(*GUILD_CHAT_MAIN)

        def find_boss(index):
            boss_locs = screen_processor.abs_search_multi("boss_txt.png", precision=0.94)
            # Sort by y axis
            boss_locs.sort(key=lambda x: x[1])
            logger.info(boss_locs)
            if len(boss_locs) == 0:
                time.sleep(1)
                return find_boss(0)

            # for loc in boss_locs:
            index = min(index, len(boss_locs) - 1)

            loc = boss_locs[index]
            emu_manager.mouse_click(loc[0], loc[1]-30, sleep=3)
            boss_panel = screen_processor.abs_search("de_boss_panel.png")
            timer = screen_processor.abs_search("de_boss_timer.png")
            logger.info("{} {}".format(boss_panel, timer))
            if boss_panel[0] != -1 and timer[0] != -1:
                logger.info("Found legit boss!")
                # Legit boss!
                return True
            else:
                logger.info("Boss has been attacked or we clicked the wrong boss!")
                # Close panel
                emu_manager.mouse_click(1132, 86)
                time.sleep(1)
                # Open chat again
                if screen_processor.abs_search("sidebar_chat.png", SIDEBAR_BOX, precision=0.85)[0] == -1:
                    emu_manager.mouse_click(*MESSAGE_ICON_MAIN, sleep=1.5)
                    emu_manager.mouse_click(*GUILD_CHAT_MAIN)
                return find_boss(index+1)

        find_boss(0)
        # Start spamming join button
        start = time.time()
        while time.time() - start < 90:
            emu_manager.mouse_click(*DE_BOSS_FIGHT)
            if screen_processor.abs_search("gather_sign.png", precision=0.9)[0] != -1:
                return True

        if screen_processor.abs_search("de_boss_panel.png")[0] != -1:
            # Close panel
            emu_manager.mouse_click(1132, 86)
        time.sleep(5)
        # Make sure that we're not accidentally in boss fight
        return screen_processor.abs_search("gather_sign.png", precision=0.9)[0] != -1


import sys
if __name__ == "__main__":
    restart = int(sys.argv[1])
    from concurrent.futures import ThreadPoolExecutor, as_completed
    start_time = time.time()
    run_time = bot_cfg.get_run_time_in_seconds()
    hwnd = set_up()

    demon_encounter = DemonEncounter()
    logger.info("Starting demon encounter bot...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(demon_encounter.start, restart),
                   executor.submit(demon_encounter.kill_popups, run_time, start_time=start_time)}

        for f in as_completed(futures):
            rs = f.result()
