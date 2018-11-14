import shiki_utils
from base_task import BaseTask
from main import *

logger = util.get_logger()

class SBoss(BaseTask):

    def __init__(self, start_time, duration, boss_count):
        super(BaseTask, self).__init__()
        self.start_time = start_time
        self.duration = duration
        self.boss_target = boss_count

    def start(self, restart=False):
        boss_found = False
        boss_count = 0
        while time.time() - self.start_time < self.duration or boss_count >= self.boss_target:
            while True:
                screen_processor.wait("dungeon_fight.png", click=True)
                screen_processor.wait("auto_icon.png", (0, WINDOW_HEIGHT - 300, 300, WINDOW_HEIGHT))
                # screen_processor.wait_disappear("auto_icon.png", (0, WINDOW_HEIGHT - 300, 300, WINDOW_HEIGHT))
                while screen_processor.abs_search("dungeon_fight.png")[0] == -1:
                    emu_manager.mouse_click(630, 550)
                    time.sleep(1)

                boss_pos = screen_processor.abs_search("sboss_found_2.png")
                if boss_pos[0] != -1:
                    logger.info("Found boss!")
                    time.sleep(1)
                    emu_manager.mouse_click(boss_pos[0]-200, boss_pos[1]-20)
                    boss_found = True
                    break
                emu_manager.mouse_click(960, 500)

            # if boss_found:
            #     FINISHED_MAIN_LOOP[0] = True
            #     return
            self.fight_boss()
            boss_count += 1
            
        FINISHED_MAIN_LOOP[0] = True

    def fight_boss(self):
        # screen_processor.wait("sboss_my.png", precision=0.94, click=True)
        boss_killed = False
        screen_processor.wait("sboss_reward_lantern.png")
        if screen_processor.abs_search("sboss_5_star.png",(96, 209, 212, 317), precision=0.94)[0] != -1:
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
                self.fight_boss()

            screen_processor.wait("realm_back_btn.png")
            emu_manager.mouse_click(*BATTLE_START_BTN)
            screen_processor.wait("auto_icon.png")

            # Battle stuff
            while screen_processor.abs_search("auto_icon.png")[0] != -1:
                decoy = screen_processor.abs_search("decoy_debuff.png", (600, 350, 800, 500))
                if decoy[0] != -1:
                    emu_manager.mouse_click(decoy[0] + 20, decoy[1] + 30)
                time.sleep(1.5)

            screen_processor.wait("sboss_fight_end.png")
            time.sleep(1.5)
            boss_killed = screen_processor.abs_search("sboss_win.png", precision=0.93)[0] != -1

            while screen_processor.abs_search("sboss_reward_lantern.png", precision=0.94)[0] == -1:
                emu_manager.mouse_click(630, 550)
                time.sleep(1.5)

        emu_manager.mouse_click(*SBOSS_CLOSE_POPUP, sleep=1)
        # TODO change this with image
        emu_manager.mouse_click(103, 666, sleep=1.5)
        emu_manager.mouse_click(273, 392)


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
    hwnd = set_up()

    sboss = SBoss(start_time, run_time, boss_count)
    logger.info("Starting demon encounter bot...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(sboss.start, restart),
                   executor.submit(sboss.kill_popups, run_time, start_time=start_time)}

        for f in as_completed(futures):
            rs = f.result()

