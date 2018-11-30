import shiki_utils
from main import *

logger = util.get_logger()


class NeitherGate:
    def __init__(self):
        pass

    def start(self):
        if not is_in_town():
            logger.info("Restarting game...")
            restart_game()
            go_to_town()
            time.sleep(5)

        # shiki_utils.soul_change("tamamo.png", "nura_soulset.png")
        time.sleep(3)

        # Click on Hunt lantern
        emu_manager.mouse_click(*HUNT_LANTERN)
        screen_processor.wait("neither_gate.png", click=True)
        time.sleep(3)
        # Click Fight
        logger.info("Engaging...")
        emu_manager.mouse_click(*NEITHER_GATE_FIGHT)
        time.sleep(3)
        logger.info("Creating party...")
        emu_manager.mouse_click(*PARTY_START)

        screen_processor.wait("realm_back_btn.png")
        logger.info("Starting battle...")

        select_team()

        while screen_processor.abs_search("auto_icon.png", (0, WINDOW_HEIGHT - 300, 300, WINDOW_HEIGHT))[0] == -1:
            # Ensure we clicked Start Battle
            emu_manager.mouse_click(*BATTLE_START_BTN)

        while screen_processor.abs_search("auto_icon.png", (0, WINDOW_HEIGHT - 300, 300, WINDOW_HEIGHT))[0] != -1:
            time.sleep(60)

        logger.info("Finished!")
        FINISHED_MAIN_LOOP[0] = True


if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor, as_completed
    start_time = time.time()
    run_time = bot_cfg.get_run_time_in_seconds()
    hwnd = set_up()

    logger.info("Starting neither gate bot...")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(NeitherGate().start),
                   executor.submit(kill_popups, run_time, start_time=start_time)}

        for f in as_completed(futures):
            rs = f.result()

