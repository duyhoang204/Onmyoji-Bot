from main import *

logger = util.get_logger()


class BaseTask:
    def __init__(self):
        pass

    def start(self, restart=False):
        pass

    def kill_popups(self, run_time, start_time=time.time()):
        logger.info("Start hunting for in-game popup...")
        while not FINISHED_MAIN_LOOP[0]:
            if screen_processor.abs_search("wanted_4.png", WANTED_2_SEARCH_BOX)[0] != -1:
                # Deny wanted req
                logger.info("WANTED FOUND!")
                emu_manager.mouse_click(*WANTED_CANCEL)
            idle = screen_processor.abs_search("wait.png", precision=0.94)
            if idle[0] != -1:
                # App not responding
                logger.info("Idling!")
                emu_manager.mouse_click(idle[0], idle[1]-20)
            time.sleep(1)
        logger.info("End hunting for in-game popup.")