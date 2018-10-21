import screen_processor
from common import *

# Constants
GLOBAL_MAP = 0
MAP_PANEL_DISPLAY = 1
REALM_SCREEN = 2

MAX_TICKETS = 30

# Coords of ticket areas
TICKET_AREAS = [
    (715, 40, 839, 85),
    (895, 35, 1025, 75),
    (359, 616, 492, 673)
]


class Realm:
    def __init__(self, target_ticket=30):
        self.target_ticket = int(target_ticket)

        start_point = REALM_ROOT_POINT
        w = REALM_PANEL_WIDTH
        h = REALM_PANEL_HEIGHT
        self.regions = [[0 for x in range(0, 3)] for y in range(0, 3)]

        # Populate regions coordinates
        for i, col in enumerate(self.regions):
            for j, row in enumerate(self.regions[i]):
                self.regions[i][j] = (start_point[0] + w * j, start_point[1] + h * i, start_point[0] + w * (j + 1),
                                 start_point[1] + h * (i + 1))

    def get_center_point(self, col, row):
        loc = self.regions[col][row]
        return loc[0] + (loc[2] - loc[0])/2, loc[1] + (loc[3] - loc[1])/2

    def is_max_tickets(self, scr_idx):
        if 0 > scr_idx > len(TICKET_AREAS):
            raise ValueError

        return self.target_ticket == 0 \
               or screen_processor.find_text("{}.0/".format(self.target_ticket), *(TICKET_AREAS[scr_idx])) \
               or screen_processor.find_text("{}/".format(self.target_ticket), *(TICKET_AREAS[scr_idx])) \
               or screen_processor.find_text("so/", *(TICKET_AREAS[scr_idx]))
