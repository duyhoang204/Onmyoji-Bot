import subprocess
import time
import win32gui

from bot_config import BotConfig
from common import EMULATOR_CONFIGS

NOX_ADB_PATH = BotConfig().get_emulator_path()
EMU_ID = BotConfig().get_property("Emulator", "use_device")


def mouse_click(x, y, sleep=0.2):
    subprocess.Popen("{} shell input tap {} {}".format(get_adb_prefix(), x, y))
    time.sleep(sleep)


def mouse_drag(x1, y1, x2, y2, duration=1500):
    subprocess.Popen("{} shell input swipe {} {} {} {} {}".format(get_adb_prefix(), x1, y1, x2, y2, duration))


def get_adb_prefix():
    return "\"{}\\bin\\adb\" -s {}".format(NOX_ADB_PATH, EMULATOR_CONFIGS.get(EMU_ID).get("id"))

def get_instance(index, force_start=True):
    win_title = "NoxPlayer" if index == 0 else "NoxPlayer{}".format(index)
    hwnd = win32gui.FindWindow(None, win_title)
    if not hwnd:
        # Try to get any Nox instance we can find
        def callback(hwnd, hwnd_list):
            if win32gui.GetClassName(hwnd) == "Qt5QWindowIcon" or "NoxPlayer" in win32gui.GetWindowText(hwnd):
                hwnd_list.append(hwnd)

        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        if len(hwnd) > 0:
            return hwnds[0]

    return hwnd


def quit_application(package_name):
    subprocess.Popen("{} shell am force-stop {}".format(get_adb_prefix(), package_name))

def is_running(package_name):
    p = subprocess.Popen("{} shell ps".format(get_adb_prefix()), stdout=subprocess.PIPE)
    out, err = p.communicate()
    return package_name in str(out)

def start_app(package_name):
    if is_running(package_name):
        return

    subprocess.Popen(
        "{} shell monkey -p {} -c android.intent.category.LAUNCHER 1".format(get_adb_prefix(), package_name),
        stdout=subprocess.PIPE)

    return is_running(package_name)
