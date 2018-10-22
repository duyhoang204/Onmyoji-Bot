import subprocess
import sys
import traceback
import win32gui

import win32con

import bot_config
from bot_config import BotConfig
from common import *
import emu_manager
import time
import screen_processor
import util
from realm import Realm, TICKET_AREAS, MAP_PANEL_DISPLAY, MAX_TICKETS

FINISHED_MAIN_LOOP = [False]
debug = 0

bot_cfg = BotConfig()
realm_obj = Realm(bot_cfg.get_property("Realm", "target_ticket"))

logger = util.get_logger()


def set_up():
    logger.info("Setting up emulator...")
    # Find Nox and bring to foreground
    hwnd = emu_manager.get_instance(int(bot_cfg.get_property("Emulator", "use_device")))

    if not hwnd:
        logger.info("ERROR!!! Could not get Nox instance")
        return

    logger.info("Got Nox player!")
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    # logger.info("Got Nox player 1!")

    win32gui.SetActiveWindow(hwnd)
    # logger.info("Got Nox player 2!")

    # win32gui.SetForegroundWindow(hwnd)
    # logger.info("Got Nox player 3!")

    win32gui.MoveWindow(hwnd, 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, True)
    return hwnd


def restart_game():
    # Close app then restart loop
    emu_manager.quit_application(APP_PKG_NAME)
    time.sleep(2)
    emu_manager.mouse_click(1228, 758)
    logger.info("Check if game is running..".format(APP_PKG_NAME))
    if not emu_manager.is_running(APP_PKG_NAME):
        logger.info("Game not running, starting app...".format(APP_PKG_NAME))
        emu_manager.start_app(APP_PKG_NAME)
        logger.info("App started successfully.")
        logger.info("Navigating to explore screen...")
        go_to_explore_screen()
        logger.info("Done setting up.")


def enter_map():
    # Show map panel
    while True:
        pos = screen_processor.abs_search("enter_map.png", ENTER_MAP_BOX)
        if pos[0] != -1:
            util.click_image("enter_map.png", (pos[0], pos[1]))
            break

        # Click on map 20
        emu_manager.mouse_click(MAP_20[0], MAP_20[1])
        time.sleep(0.5)
    # mouse_click(EXPLORE_BUTTON[0], EXPLORE_BUTTON[1])
    screen_processor.wait("paper_dude.png", PAPER_DUDE_BOX, sleep=1)


def find_mobs_with_buff(buff="exp", fight_boss=False):
    if fight_boss:
        boss_pos = screen_processor.abs_search("boss.png", BOSS_SEARCH_BOX)
        if boss_pos[0] != -1:
            return boss_pos, True

    for k in range(0, 2):
        for i in range(1, 7):
            # Decrease precision here?
            pos = screen_processor.abs_search("{}_icon_{}.png".format(buff, i), precision=0.85)
            if pos[0] != -1:
                # Find the closest fight icon in a rectangle surrounding the mob
                x0 = pos[0] - MOB_BOX[0] / 2 + 15  # add some offset
                y0 = pos[1] - MOB_BOX[1]
                x1 = pos[0] + MOB_BOX[0] / 2 + 15  # add some offset
                y1 = pos[1]
                mob_rectangle = (x0, y0, x1, y1)

                fight_pos = screen_processor.abs_search("fight.png", mob_rectangle)
                if fight_pos[0] != -1:
                    # mouse_click(fight_pos[0], fight_pos[1])
                    return fight_pos, False
    return (-1, -1), False


def find_mobs_with_buff_v2(buff="exp", fight_boss=False):
    if fight_boss:
        boss_pos = screen_processor.abs_search("boss.png", BOSS_SEARCH_BOX)
        if boss_pos[0] != -1:
            return boss_pos, True

    # Find all fight icons first
    locs = sorted(screen_processor.abs_search_multi("fight.png", EXP_SEARCH_REGION, precision=0.98), key=lambda x: x[0])
    for loc in locs:
        # for k in range(0, 2):
        for i in range(1, 7):
            # Decrease precision here?
            pos = screen_processor.abs_search("{}_icon_{}.png".format(buff, i),
                                              (loc[0]-170, loc[1], loc[0]+170, loc[1]+250),
                                              precision=0.8)
            if pos[0] != -1:
                return loc, False

    return (-1, -1), False


def process_battle(mob_pos, is_boss):
    # Unlock team so we can replace farm materials later
    util.find_and_click("lock.png", LOCK_BTN_BOX, double_click=False)

    # Click on Fight
    util.click_image("fight.png", mob_pos)

    # Wait for the back button to appear
    try:
        screen_processor.wait("team_battle.png", sleep=0.3, click=False, wait_count=50)
        screen_processor.wait("realm_back_btn.png", sleep=0.3, click=False, wait_count=50)
    except screen_processor.ImageNotFoundException:
        # We possibly missed the fight button, just return
        return

    # Check for max level materials
    need_replace = []
    for i in range(0, 2):
        mat_pos = screen_processor.abs_search("max_lvl_1.png", FOOD_LOC_BATTLE[i])
        # logger.info("Index {} {}".format(i, mat_pos))
        if mat_pos[0] != -1:
            need_replace.append(i)
    if len(need_replace) > 0:
        # Click on the change team area
        emu_manager.mouse_click(CHANGE_TEAM_POS[0], CHANGE_TEAM_POS[1])
        emu_manager.mouse_click(CHANGE_TEAM_POS[0], CHANGE_TEAM_POS[1])
        time.sleep(2)

        # "ALL" button
        emu_manager.mouse_click(68, 690, sleep=1)
        food_type = bot_cfg.get_property("General", "food_type")
        food_coord = FOOD_OPTIONS.get(food_type)
        if not food_coord:
            raise bot_config.InvalidConfiguration

        emu_manager.mouse_click(*food_coord, sleep=1)

        # screen_processor.wait("food_slide_bar.png", click=False)

        for item in need_replace:
            # Process replacing materials
            process_replace_v2(item, food_type)

        # Press return
        emu_manager.mouse_click(35, 60)
        time.sleep(1.5)

    while screen_processor.abs_search("auto_icon.png", (0, WINDOW_HEIGHT - 300, 300, WINDOW_HEIGHT))[0] == -1:
        # Ensure we clicked Start Battle
        emu_manager.mouse_click(*BATTLE_START_BTN)

    # Start spamming target for at least 5 seconds
    start = time.time()
    spam_time = 10 if is_boss else 5
    while time.time() - start < spam_time:
        # Target the left most monster in the front row. This is for single target shiki like Irabaki
        emu_manager.mouse_click(623, 210)

    while screen_processor.abs_search("auto_icon.png", (0, WINDOW_HEIGHT - 300, 300, WINDOW_HEIGHT))[0] != -1:
        time.sleep(1)

    if is_boss:
        while screen_processor.abs_search("back.png", BACK_BTN_BOX)[0] == -1:
            time.sleep(0.5)
            # Click center of the screen with some offset
            emu_manager.mouse_click(663, 317)

        logger.info("Won boss battle, searching for rewards...")
        time.sleep(5)
        for i in range(0, 4):
            if screen_processor.abs_search("boss_reward.png", click=True)[0] != -1:
                logger.info("Got boss reward #{}".format(i))
                time.sleep(1)
                # Click outside to close reward popup
                emu_manager.mouse_click(675, 560)
                time.sleep(1)
            else:
                break
        # Wait a bit for it to go back to map
        time.sleep(5)
        while screen_processor.abs_search("buff_btn.png", BUFF_BTN_BOX)[0] == -1:
            # If we can't find buff btn here, probably we missed some rewards. Manually click back
            util.click_image("back.png", (16, 71))
            # Confirm exit map
            emu_manager.mouse_click(EXIT_MAP_OK_BTN[0], EXIT_MAP_OK_BTN[1])

        logger.info("Got back to map from boss battle!")
        return

    logger.info("Ending battle, waiting for map...")
    # Wait for map
    while screen_processor.abs_search("battle_reward.png")[0] == -1:
        # Click center of the screen with some offset
        emu_manager.mouse_click(663, 317)
        time.sleep(0.5)

    while screen_processor.abs_search("battle_reward.png")[0] != -1:
        emu_manager.mouse_click(663, 317)
        time.sleep(0.5)

    screen_processor.wait("back.png", BACK_BTN_BOX)

    logger.info("Got back to map from battle!")


def process_replace(index):
    logger.info("Processing replacing materials!")
    if 0 < index > 1:
        raise ValueError

    # Find a card that's not maxed out,, or locked, or is blue daruma, or is currently in fight
    while screen_processor.abs_search("max_lvl.png", LAST_CHARACTER_LEVEL_REGION)[0] != -1 \
            or screen_processor.abs_search("in_fight.png", LAST_CHARACTER_LEVEL_REGION)[0] != -1 \
            or screen_processor.abs_search("blue_daruma.png", LAST_CHARACTER_LEVEL_REGION)[0] != -1 \
            or screen_processor.abs_search("locked_food.png", LAST_CHARACTER_LEVEL_REGION)[0] != -1:
        emu_manager.mouse_drag(LAST_CHARACTER_CENTER[0], LAST_CHARACTER_CENTER[1],
                               LAST_CHARACTER_CENTER[0] - CHARACTER_CARD_BOX[0], LAST_CHARACTER_CENTER[1], duration=700)
        time.sleep(0.7)
    time.sleep(1)
    # Drag into team
    emu_manager.mouse_drag(LAST_CHARACTER_CENTER[0], LAST_CHARACTER_CENTER[1], FOOD_LOC_CHANGE[index][0],
                           FOOD_LOC_CHANGE[index][1], duration=1000)
    time.sleep(2)
    logger.info("Changed character #{}".format(index))
    # Move on to the next card
    emu_manager.mouse_drag(LAST_CHARACTER_CENTER[0], LAST_CHARACTER_CENTER[1],
                           LAST_CHARACTER_CENTER[0] - CHARACTER_CARD_BOX[0], LAST_CHARACTER_CENTER[1], duration=700)
    time.sleep(1)

def process_replace_v2(index, food_type="daruma"):
    def drag_to_first(x1,y1,x2,y2, length):
        emu_manager.mouse_drag(x1,
                               y1 + 30,  # offset for title bar
                               x2,
                               y2 + 30,
                               duration=length * 700)
        time.sleep(length * 0.9)

    if food_type != "daruma":
        process_replace(index)
    else:
        # First, filter all locked food
        while True:
            locked = screen_processor.abs_search_multi("locked_food.png", FOOD_SEARCH_REGION, precision=0.9)
            if locked:
                locked.sort(key=lambda x: x[0], reverse=True)
                # Find the right most food
                last = locked[0]
                # Drag in out
                drag_to_first(last[0],
                               last[1],
                               85,
                               last[1],
                               len(locked))
            else:
                break

        # Do the same with blue daruma, maxed or in-fight food, but one at a time
        while True:
            # Search for maxed food
            maxed = screen_processor.abs_search_multi("max_lvl.png", FOOD_SEARCH_REGION, precision=0.9)
            maxed.sort(key=lambda x: x[0], reverse=True)

            if len(maxed) > 0 and maxed[-1][0] < FIRST_CHARACTER_LEVEL_REGION[2]:
                last = maxed[0]
                # Drag all of the maxed's out
                drag_to_first(last[0],
                              last[1],
                              85,
                              last[1],
                              len(maxed))
                continue

            # Food that is currently in battle
            in_fight = screen_processor.abs_search("in_fight.png", FIRST_CHARACTER_LEVEL_REGION)
            if in_fight[0] != -1:
                drag_to_first(in_fight[0],
                              in_fight[1],
                              in_fight[0] - CHARACTER_CARD_BOX[0],
                              in_fight[1],
                              1)
                continue

            # Don't farm blue daruma
            # TODO make this configurable?
            blue_drm = screen_processor.abs_search("blue_daruma.png", FIRST_CHARACTER_LEVEL_REGION)
            if blue_drm[0] != -1:
                drag_to_first(blue_drm[0],
                              blue_drm[1],
                              blue_drm[0] - CHARACTER_CARD_BOX[0],
                              blue_drm[1],
                              1)
                continue

            # We're good here, quit looping
            break

        # Finally, we found a food to replace!
        time.sleep(0.5)
        # First drag it out of the "stack" position to avoid a bug which will take a food in the thrash stack
        # instead of the valid food
        emu_manager.mouse_drag(FIRST_CHARACTER_CENTER[0], FIRST_CHARACTER_CENTER[1], FIRST_CHARACTER_CENTER[0]+200,
                               FIRST_CHARACTER_CENTER[1], duration=1000)
        time.sleep(1.5)
        # Then drag it into team
        emu_manager.mouse_drag(FIRST_CHARACTER_CENTER[0]+200, FIRST_CHARACTER_CENTER[1], FOOD_LOC_CHANGE[index][0],
                               FOOD_LOC_CHANGE[index][1], duration=1000)
        logger.info("Changed character #{}".format(index))
        time.sleep(2)

def buff_on(buffs=list()):
    logger.info("Turning on buffs...")
    if len(buffs) == 0 or "0" in buffs:
        return
    # Click on buff
    buff_btn = screen_processor.wait("buff_btn.png", BUFF_BTN_BOX, click=False)
    emu_manager.mouse_click(buff_btn[0], buff_btn[1] - 30, sleep=1.5)
    logger.info("Clicked buff")
    for buff in buffs:
        buff_pos = screen_processor.abs_search("buff_exp_{}.png".format(buff.strip()), precision=0.7)
        # Retry
        if buff_pos[0] == -1:
            try:
                buff_pos = screen_processor.abs_search("buff_exp_{}_1.png".format(buff.strip()), precision=0.7)
            except:
                pass

        if buff_pos[0] != -1:
            pos = screen_processor.abs_search("buff_play.png", (buff_pos[0], buff_pos[1] - 50, 950, buff_pos[1] + 70),
                                              precision=0.7)
            # logger.info("====== {}".format((buff_pos[0], buff_pos[1]-30, 950 ,buff_pos[1]+30)))
            if pos[0] != -1:
                # Turn it on
                logger.info("Turning on buff {} at {}".format(buff, pos))
                emu_manager.mouse_click(pos[0] + 5, pos[1] + 5)
                time.sleep(0.5)
            else:
                logger.info("Buff {} already on!".format(buff))

    # Close buff pop up
    emu_manager.mouse_click(buff_btn[0], buff_btn[1] - 5, sleep=1)


def buff_off(buffs=list()):
    logger.info("Turning off buffs...")
    if len(buffs) == 0 or "0" in buffs:
        return

    buff_btn = screen_processor.wait("buff_btn.png", BUFF_BTN_BOX, click=False, sleep=1)
    emu_manager.mouse_click(buff_btn[0], buff_btn[1] - 30, sleep=1.5)
    logger.info("Clicked buff")
    # Probably have no more than 10 buffs
    for x in range(0, 10):
        pos = screen_processor.abs_search("buff_pause.png", precision=0.7)
        if pos[0] != -1:
            emu_manager.mouse_click(pos[0] + 5, pos[1] + 5)
            time.sleep(0.7)
        else:
            break
    # Close
    emu_manager.mouse_click(buff_btn[0], buff_btn[1] - 5, 1)


def main_task(run_time, start_time=time.time(), hwnd=None):
    try:
        do_main_loop(run_time=run_time, start_time=start_time, hwnd=hwnd)
    except:
        # Exit the game
        logger.error("!!!! BOT HAS COUNTER SOME ERROR!!! QUITTING...")
        e_type, val, tb = sys.exc_info()
        traceback.print_exception(e_type, val, tb, limit=10, file=sys.stdout)
        if not debug:
            restart_game()
            do_main_loop(run_time, start_time)


def do_main_loop(run_time, start_time=time.time(), hwnd=None):
    logger.info("Starting main task...")
    # test()
    time.sleep(1)
    mystic_shop_ts = 0

    # Turn on buff
    buffs = bot_cfg.get_buff_config()
    buff_on(buffs)
    while time.time() - start_time < run_time:
        # Show map panel
        while True:
            pos = screen_processor.abs_search("enter_map.png", ENTER_MAP_BOX)
            if pos[0] != -1:
                break

            # Click on map 20
            emu_manager.mouse_click(MAP_20[0], MAP_20[1])
            time.sleep(0.5)

        # Check for payk
        payk_config = bot_cfg.get_payk_images()
        payk_arr = payk_config.split(',') if payk_config else []
        for payk_img in payk_arr:
            payk_img = payk_img.strip() + ".png"
            if screen_processor.abs_search(payk_img)[0] != -1:
                # Close map popup
                emu_manager.mouse_click(1042, 182)
                time.sleep(1)
                # Click again
                screen_processor.abs_search(payk_img, click=True)

                # while screen_processor.abs_search("payk_fight_btn.png", click=True)[0] == -1:
                time.sleep(3)

                # if screen_processor.abs_search("payk_fight_btn.png", click=True)[0] != -1:
                def create_party():
                    logger.info("Creating party for payk...")
                    emu_manager.mouse_click(*PAYK_FIGHT)
                    time.sleep(1)
                    emu_manager.mouse_click(*PARTY_INVITE_ALL)
                    emu_manager.mouse_click(*PARTY_CREATE_BTN)
                    party_start = time.time()
                    while screen_processor.abs_search("realm_back_btn.png")[0] == -1:
                        emu_manager.mouse_click(*PARTY_START)
                        time.sleep(3)
                        if (time.time() - party_start) > PARTY_TIME_SECOND:
                            # No one joined our party :(
                            logger.info("No one joined, creating new party... :(")
                            if screen_processor.abs_search("payk_scroll.png")[0] != -1:
                                # Still legit? Retry
                                return create_party()
                            else:
                                # Click on map 20
                                emu_manager.mouse_click(MAP_20[0], MAP_20[1])
                                return False
                    logger.info("Party created successfully!")
                    return True

                if not create_party():
                    logger.info("Create party failed for {}. Skip to next payk search...".format(payk_img))
                    continue

                logger.info("Starting payk battle..")
                emu_manager.mouse_click(*BATTLE_START_BTN)

                # Wait for map
                time.sleep(2)
                while screen_processor.abs_search("auto_icon.png")[0] != -1:
                    time.sleep(2)
                while screen_processor.abs_search("back.png", BACK_BTN_BOX)[0] == -1:
                    emu_manager.mouse_click(*MAP_20)

                logger.info("Got back to map from payk battle!")

        # Check for shop
        if time.time() - mystic_shop_ts > 60 * 30 \
                and screen_processor.abs_search("mystic_shop.png")[0] != -1:
            # Close map popup
            emu_manager.mouse_click(1042, 182)
            time.sleep(1)
            # Click again
            screen_processor.abs_search("mystic_shop.png", click=True)
            # Wait for camera to pan
            time.sleep(3)

            items = bot_cfg.get_property("General", "mystic_shop_items").split(",")
            for item in items:
                image = item.strip() + ".png"
                if screen_processor.abs_search(image, click=True)[0] != -1:
                    time.sleep(1)

                    # Click confirm
                    logger.info("Click 1")
                    screen_processor.abs_search("base_btn_corner.png", click=True)
                    time.sleep(1.5)
                    # Click outside to close popup
                    logger.info("Click 2")

                    emu_manager.mouse_click(666, 646)

            # Go back to map
            emu_manager.mouse_click(54, 87)

            mystic_shop_ts = time.time()
            continue

        # Check for chest
        if screen_processor.abs_search("chest.png")[0] != -1:
            # Close map popup
            emu_manager.mouse_click(1042, 182)
            time.sleep(1)
            # Click again
            screen_processor.abs_search("chest.png", click=True)
            time.sleep(5)
            while screen_processor.abs_search("enter_map.png", ENTER_MAP_BOX)[0] == -1:
                # Click on map 20
                emu_manager.mouse_click(MAP_20[0], MAP_20[1])

            continue

        # Check for realm tickets
        if realm_obj.is_max_tickets(MAP_PANEL_DISPLAY):
            if int(bot_cfg.get_property("Realm", "stop_map_farming_when_full_ticket")):
                # Quit farming
                logger.info("Realm tickets are full! Quitting farming..")
                break
            if bot_cfg.get_property("Realm", "auto_farm"):
                time.sleep(1)
                emu_manager.mouse_click(1050, 174, 1)
                enter_realm(start_time, run_time)
                if time.time() - start_time > run_time:
                    # Finish
                    break

        # emu_manager.mouse_click(1050, 174, 1)
        # enter_realm(start_time, run_time)
        # if time.time() - start_time > run_time:
        #     # Finish
        #     break

        enter_map()
        move_screen = 0
        fight_boss = BotConfig().should_fight_boss()
        just_battled = False
        battle_count = 0
        while True:
            if fight_boss and battle_count >=3 and just_battled:
                # Wait on screen a little bit in case boss appears
                time.sleep(1 + move_screen * 0.1)
            mob_pos, is_boss = find_mobs_with_buff_v2(fight_boss=(fight_boss and battle_count >=3))
            if mob_pos[0] != -1:
                # Found mob!
                process_battle(mob_pos, is_boss)
                battle_count += 1
                just_battled = True
                if is_boss:
                    # Finished this map
                    break
            elif move_screen < 2:
                # Move the screen to look for more mobs
                # TODO remove hard code here
                emu_manager.mouse_drag(WINDOW_WIDTH-100, 90, 100, 90, duration=700)
                time.sleep(1.2)
                move_screen += 1
                just_battled = False
            else:
                # We probably couldn't find any mobs in this map, just quit then try again!
                util.click_image("back.png", (16, 71))
                # Confirm exit map
                emu_manager.mouse_click(EXIT_MAP_OK_BTN[0], EXIT_MAP_OK_BTN[1])
                screen_processor.wait("buff_btn.png", BUFF_BTN_BOX, click=False)
                break

    time.sleep(3)
    logger.info("Ended main loop. Ran for {} seconds".format(time.time() - start_time))

    # Turn off exp buff
    buff_off(buffs)
    FINISHED_MAIN_LOOP[0] = True


def kill_popups(run_time, start_time=time.time()):
    logger.info("Start hunting for in-game popup...")
    while not FINISHED_MAIN_LOOP[0]:
        if screen_processor.abs_search("wanted_4.png", WANTED_2_SEARCH_BOX)[0] != -1:
            # Deny wanted req
            logger.info("WANTED FOUND!")
            emu_manager.mouse_click(*WANTED_CANCEL)
        elif screen_processor.abs_search("friend_popup.png", FRIEND_POPUP_SEARCH_BOX, precision=0.9)[0] != -1:
            logger.info("FRIEND POPUP FOUND!")
            emu_manager.mouse_click(*FRIEND_POPUP_CANCEL)
        elif screen_processor.abs_search("sidebar_chat.png", SIDEBAR_BOX, precision=0.85)[0] != -1:
            logger.info("SIDEBAR CHAT PANEL FOUND!")
            emu_manager.mouse_click(*SIDEBAR_CHAT_BTN)

        time.sleep(1)
    logger.info("End hunting for in-game popup.")


def close_teamviewer_modal(run_time, start_time=time.time()):
    logger.info("Start hunting for teamviewer popup..")
    while not FINISHED_MAIN_LOOP[0]:
        hwnd = win32gui.FindWindow("#32770", None)
        if hwnd:
            win32gui.CloseWindow(hwnd)
        time.sleep(5)
    logger.info("End hunting for teamviewer popup")


def check_main_task_ended(run_time, start_time=time.time()):
    logger.info("Start checking for main task...")
    while (time.time() - start_time) < (run_time + 300):
        time.sleep(10)

    if not FINISHED_MAIN_LOOP[0]:
        logger.info("WE GOT STUCK!!! ABORT TO SAVE THE BUFFS!!!")
        if not debug:
            emu_manager.quit_application(APP_PKG_NAME)
    logger.info("Finished checking for main task.")


def enter_realm(start_time, run_time):
    # Turn off buffs
    buffs = bot_cfg.get_buff_config()
    buff_off(buffs)
    # Close map panel
    emu_manager.mouse_click(1041, 182, sleep=1)
    # Click on realm
    emu_manager.mouse_click(307, 683)
    screen_processor.wait("realm_reward_icon.png")

    try:
        current_tickets = int(screen_processor.get_text(370, 590, 515, 670).split("/")[0])
    except:
        current_tickets = realm_obj.target_ticket

    # Find current win streak
    # win_streak = len(screen_processor.abs_search_multi("realm_win.png", precision=0.967)) + \
    #              len(screen_processor.abs_search_multi("realm_win_1.png", precision=0.96))

    win_streak = 0
    for i, col in enumerate(realm_obj.regions):
        for j, row in enumerate(realm_obj.regions[i]):
            if screen_processor.abs_search("realm_win.png", row)[0] != -1 or \
            screen_processor.abs_search("realm_win_1.png", row)[0] != -1:
                win_streak += 1

    logger.info("Win streak: {}".format(win_streak))
    while True:
        has_lost = False
        for i, col in enumerate(realm_obj.regions):
            for j, row in enumerate(realm_obj.regions[i]):
                try:
                    win, did_battle = do_realm_battle(i, j, row, win_streak)
                    # Check if won
                    if not win and bot_cfg.get_property("Realm", "do_retry"):
                        win, did_battle = do_realm_battle(i, j, row, win_streak, retry=True)

                    # Deduct ticket count
                    if win and did_battle:
                        current_tickets = current_tickets - 1
                        win_streak += 1
                        logger.info("Current tickets: {}".format(current_tickets))

                    has_lost |= not win
                except CannotAttackRealmException:
                    # Probably ran out of tickets
                    current_tickets = 0
                    # Close attack popup
                    emu_manager.mouse_click(1180, 95, 1)

                if current_tickets == 0 or ((time.time() - start_time) > run_time):
                    # Close realm screen
                    emu_manager.mouse_click(1180, 95, 1)
                    # Turn the buffs back on to continue farming
                    buff_on(buffs)
                    return

        if has_lost:
            logger.info("We have lost some realm attack :( Refreshing opponents..")
            emu_manager.mouse_click(1045, 568, 1)
            emu_manager.mouse_click(746, 461, 1)

        time.sleep(2)


class CannotAttackRealmException(BaseException):
    pass


def do_realm_battle(i, j, row, win_streak, retry=False):
    if not retry:
        win = screen_processor.abs_search("realm_win.png", row)[0] != -1 or \
              screen_processor.abs_search("realm_win_1.png", row)[0] != -1
        lost = screen_processor.abs_search("realm_lost.png", row)[0] != -1
        attacked = win or lost

        if attacked:
            logger.info("Game {} has been attacked! Move on.".format(i * 3 + j + 1))
            return win, False

    logger.info("Can attack game {}".format(i * 3 + j + 1))
    center_x, center_y = realm_obj.get_center_point(i, j)
    logger.info("Center: {} {}".format(center_x, center_y))
    emu_manager.mouse_click(center_x, center_y, 1)
    # emu_manager.mouse_click(center_x + 70, center_y + 150, 0.7)
    atk_btn = screen_processor.abs_search("realm_atk_btn.png", click=True)
    # Fail safe this
    if atk_btn[0] == -1:
        return False, False
    try:
        screen_processor.wait("realm_back_btn.png")
    except screen_processor.ImageNotFoundException:
        logger.info("Could not attack attack game {}! Maybe we ran out of tickets?..".format(i * 3 + j + 1))
        raise CannotAttackRealmException

    # Select team
    emu_manager.mouse_click(84, 681, 1)
    team_pos = REALM_TEAMS[0] if not retry else REALM_TEAMS[1]
    emu_manager.mouse_click(*team_pos)
    screen_processor.wait("realm_team_set.png", click=True)
    # emu_manager.mouse_click(*REALM_SELECT_TEAM_BTN)

    while screen_processor.abs_search("auto_icon.png", (0, WINDOW_HEIGHT - 300, 300, WINDOW_HEIGHT))[0] == -1:
        emu_manager.mouse_click(*BATTLE_START_BTN, sleep=3)

    win = False
    while screen_processor.abs_search("realm_reward_icon.png")[0] == -1:
        if screen_processor.abs_search("battle_reward.png")[0] != -1:
            win = True
        # Click a random place
        emu_manager.mouse_click(153, 573, sleep=1)

    current_streak = win_streak + 1 if win else 1
    if current_streak % 3 == 0:
        time.sleep(2)
        # Click outside a few times in case we have milestone reward
        emu_manager.mouse_click(153, 573, sleep=1)
        emu_manager.mouse_click(153, 573, sleep=1)

    # Check win and return
    return win, True


def go_to_explore_screen():
    # Go to explore screen from login screen
    while screen_processor.abs_search("main_scr_buff.png")[0] == -1:
        if screen_processor.abs_search("login_announcement.png", precision=0.9)[0] != -1:
            emu_manager.mouse_click(*CLOSE_ANNOUNCEMENT_BTN)
            time.sleep(1)
        time.sleep(1.5)
        emu_manager.mouse_click(*LOGIN_BTN)

    time.sleep(15)
    emu_manager.mouse_click(*EXPLORE_BTN)


if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor, as_completed
    start_time = time.time()
    run_time = bot_cfg.get_run_time_in_seconds()
    print(run_time)
    hwnd = set_up()

    logger.info("Starting bot...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(main_task, run_time, start_time=start_time, hwnd=hwnd),
                   executor.submit(kill_popups, run_time, start_time=start_time),
                   # executor.submit(close_teamviewer_modal, run_time, start_time=start_time),
                   executor.submit(check_main_task_ended, run_time, start_time=start_time)}

        for f in as_completed(futures):
            rs = f.result()

    # emu_manager.mouse_click(1050, 174, 1)
    # enter_realm(time.time(), 3600)
