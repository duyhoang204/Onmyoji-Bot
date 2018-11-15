import shiki_utils
from base_task import BaseTask
from main import *

logger = util.get_logger()

class SBoss(BaseTask):

    def __init__(self, start_time, duration, boss_count, mode):
        super(BaseTask, self).__init__()
        self.start_time = start_time
        self.duration = duration
        self.boss_target = boss_count
        self.mode = mode

    def start(self, restart=False):
        if restart:
            logger.info("Restarting game...")
            restart_game()
            go_to_main_screen()
            time.sleep(5)
            if self.mode == "leech":
                emu_manager.mouse_click(956, 466)

        boss_count = 0
        while time.time() - self.start_time < self.duration:
            if mode == 'farm':
                if boss_count >= self.boss_target:
                    break
                self.farm()
                boss_count += 1
                logger.info("Boss killed: {}".format(boss_count))
            elif mode == 'leech':
                self.leech()
            else:
                logger.error("NO MODE NAMED {}!".format(mode))
                break

        logger.info("Ended automation.")
        FINISHED_MAIN_LOOP[0] = True

    def farm(self):
        while True:
            screen_processor.wait("dungeon_fight.png", click=True)
            screen_processor.wait("auto_icon.png", (0, WINDOW_HEIGHT - 300, 300, WINDOW_HEIGHT))
            # screen_processor.wait_disappear("auto_icon.png", (0, WINDOW_HEIGHT - 300, 300, WINDOW_HEIGHT))
            while screen_processor.abs_search("dungeon_fight.png")[0] == -1:
                emu_manager.mouse_click(630, 550)
                time.sleep(0.5)
            time.sleep(1.5)
            boss_pos = screen_processor.abs_search("sboss_found_2.png")
            if boss_pos[0] != -1:
                logger.info("Found boss!")
                time.sleep(1)
                emu_manager.mouse_click(boss_pos[0] - 200, boss_pos[1] - 20)
                break
            emu_manager.mouse_click(960, 500)

        screen_processor.wait("sboss_reward_lantern.png")

        is_high_level_boss = screen_processor.abs_search("sboss_5_star.png",(96, 209, 212, 317), precision=0.94)[0] != -1 \
                            or screen_processor.abs_search("sboss_6_star.png",(96, 209, 212, 317), precision=0.94)[0] != -1
        self.fight_boss(is_high_level_boss)

        emu_manager.mouse_click(*SBOSS_CLOSE_POPUP, sleep=1)
        # TODO change this with image
        emu_manager.mouse_click(103, 666, sleep=1.5)
        emu_manager.mouse_click(522, 392)
        # emu_manager.mouse_click(273, 392)

    def leech(self):
        screen_processor.wait("sboss_reward_lantern.png")

        boss_6 = screen_processor.abs_search("sboss_6_star.png", precision=0.94)
        if boss_6[0] != -1:
            emu_manager.mouse_click(boss_6[0]+100, boss_6[1]-15)
        else:
            boss_5 = screen_processor.abs_search("sboss_5_star.png", precision=0.94)
            if boss_5[0] != -1:
                emu_manager.mouse_click(boss_5[0] + 100, boss_5[1] - 15)
            else:
                emu_manager.mouse_click(*SBOSS_CLOSE_POPUP, sleep=5)
                emu_manager.mouse_click(*SBOSS_MAP_TARGET)
                return

        self.fight_boss()

    def fight_boss(self, is_high_level_boss=False):
        # screen_processor.wait("sboss_my.png", precision=0.94, click=True)
        boss_killed = False
        attempt = 0
        if is_high_level_boss and attempt == 0:
            emu_manager.mouse_click(*SBOSS_ALLOUT_ATTACK)
        else:
            emu_manager.mouse_click(*SBOSS_NORMAL_ATTACK)
        while not boss_killed:
            emu_manager.mouse_click(*SBOSS_FIGHT)
            time.sleep(1.5)
            if screen_processor.abs_search("sboss_tea.png")[0] != -1:
                time.sleep(30)
                # Close popup
                emu_manager.mouse_click(*SBOSS_CLOSE_TEA_POPUP)
                self.fight_boss(is_high_level_boss)

            try:
                screen_processor.wait("realm_back_btn.png")
            except:
                return

            if is_high_level_boss and attempt == 0:
                select_team(3)
            else:
                select_team(2)
            emu_manager.mouse_click(*BATTLE_START_BTN)
            screen_processor.wait("auto_icon.png")

            # Battle stuff
            while screen_processor.abs_search("auto_icon.png")[0] != -1:
                decoy = screen_processor.abs_search("decoy_debuff.png", (650, 210, 750, 260))
                if decoy[0] != -1:
                    emu_manager.mouse_click(decoy[0] + 20, decoy[1] + 30)
                time.sleep(1.5)

            screen_processor.wait("sboss_fight_end.png")
            time.sleep(1.5)
            boss_killed = screen_processor.abs_search("sboss_win.png", precision=0.93)[0] != -1
            attempt += 1
            while screen_processor.abs_search("sboss_reward_lantern.png", precision=0.94)[0] == -1:
                emu_manager.mouse_click(630, 550)
                time.sleep(1.5)


import sys
if __name__ == "__main__":
    try:
        restart = int(sys.argv[1])
    except:
        restart = 0

    from concurrent.futures import ThreadPoolExecutor, as_completed
    start_time = time.time()
    run_time = bot_cfg.get_run_time_in_seconds()
    boss_count = int(bot_cfg.get_property("SBoss", "boss_count"))
    mode = bot_cfg.get_property("SBoss", "auto_mode")
    hwnd = set_up()

    sboss = SBoss(start_time, run_time, boss_count, mode)
    logger.info("Starting demon encounter bot...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(sboss.start, restart),
                   executor.submit(sboss.kill_popups, run_time, start_time=start_time)}

        for f in as_completed(futures):
            rs = f.result()

