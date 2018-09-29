import configparser
from datetime import datetime

from common import *

class BotConfig(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(CONFIGURATION_FILE_PATH)

    def get_property(self, section, key_name):
        return self.config[section].get(key_name)

    def get_section(self, section):
        return self.config[section]

    def get_run_time_in_seconds(self):
        section = self.get_section("RunTime")
        hour = int(section.get("hour"), 0)
        minute = int(section.get("minute"), 0)
        second = int(section.get("second"), 0)
        return hour*60*60 + minute*60 + second

    def get_emulator_path(self):
        section = self.get_section("Emulator")
        return section.get("path")

    def get_buff_config(self):
        section = self.get_section("General")
        return  section.get("buff").split(",")

    def should_fight_boss(self):
        return int(self.get_property("General", "fight_boss"))

    def get_payk_images(self):
        return self.get_property("General", "fight_payk")


class InvalidConfiguration(Exception):
    pass