import logging
import time
import traceback
from enum import Enum, unique
from sys import stdin
from threading import Thread
from typing import Optional

import uiautomator2 as u2
from uiautomator2 import Device
from uiautomator2.exceptions import XPathElementNotFoundError

from twistytimer.utils import xpath_consts, timer_consts, data_utils
from twistytimer.utils.timer_consts import *

exit_flag = False
global logger


@unique
class _MainTab(Enum):
    TIMER = 0
    DATA = 1
    STATISTICS = 2


@unique
class PuzzleType(Enum):
    RUBIK_2 = '222'
    RUBIK_3 = '333'
    RUBIK_4 = '444'
    RUBIK_5 = '555'
    RUBIK_6 = '666'
    RUBIK_7 = '777'
    SKEWB = 'skewb'
    MEGAMINX = 'mega'
    PYRAMINX = 'pyra'
    SQUARE_1 = 'sq'
    CLOCK = 'clock'


class SolveInfo:
    def __init__(self, puzzle: str, group: str, time: str, date: str, scramble: str, comment: str, penalty: str):
        self.puzzle = puzzle
        self.group = group
        self.time = data_utils.convert_time_str(time)
        self.date = data_utils.convert_date_str(date)
        self.scramble = scramble or ''
        self.penalty = penalty or '0'
        self.comment = comment or ''

    def __repr__(self):
        return 'time: ' + str(self.time) + ', date: ' + str(self.date) + ', scramble: ' + self.scramble \
               + ', penalty: ' + self.penalty + ', comment: ' + self.comment

    def get_insert_string(self):
        return '"' + self.puzzle + '";"' + self.group + '";"' + str(self.time) + '";"' + str(self.date) + '";"' \
               + self.scramble + '";"' + self.penalty + '";"' + self.comment + '"'


class _TwistyTimer:

    def __init__(self, device: Device):
        self.device = device

    def switch_to_timer(self) -> bool:
        return self._switch_to_tab(_MainTab.TIMER.value)

    def switch_to_data(self) -> bool:
        return self._switch_to_tab(_MainTab.DATA.value)

    def switch_to_statistics(self) -> bool:
        return self._switch_to_tab(_MainTab.STATISTICS.value)

    def _switch_to_tab(self, index: int) -> bool:
        if not self.is_main_page():
            return False

        d = self.device
        items = d.xpath(xpath_consts.MAIN_TAB_ITEM).all()
        if index > len(items) - 1:
            return False
        center = items[index].center()
        d.double_click(center[0], center[1], DOUBLE_CLICK_TIMEOUT)
        return True

    def is_main_page(self) -> bool:
        if not self.is_twisty_running():
            return False

        d = self.device
        items = d.xpath(xpath_consts.SETTING_PAGE_ITEM).all()
        return not len(items) > 0

    def twisty_start(self) -> bool:
        if not self.is_device_running():
            return False

        self.device.app_start(timer_consts.TWISTY_TIMER_APP)
        pid = self.device.app_wait(timer_consts.TWISTY_TIMER_APP)
        success = pid != 0 and self.is_twisty_running()
        if success:
            logger.info('[Current App] ' + str(self.device.app_info(timer_consts.TWISTY_TIMER_APP)))
        return success

    def twisty_stop(self) -> bool:
        if not self.is_twisty_running():
            return True
        self.device.app_stop(timer_consts.TWISTY_TIMER_APP)
        return True

    def is_twisty_running(self) -> bool:
        try:
            app_info = self.device.app_current()
            package = app_info['package']
            return package == timer_consts.TWISTY_TIMER_APP
        except OSError:
            logger.error(traceback)
            return False

    def is_device_running(self) -> bool:
        return self.device is not None


class _DataPage(_TwistyTimer, Thread):
    def __init__(self, device: Device, puzzle_type: PuzzleType = PuzzleType.RUBIK_3, group_name: str = 'Normal'):
        super().__init__(device)
        self.puzzle_type = puzzle_type
        self.group_name = group_name
        self.x1 = None
        self.y1 = None

    def opration_on_first_card(self) -> Optional[SolveInfo]:
        self.click_first_card_info()
        solve_info = self.get_solve_info()
        if solve_info is None:
            return None
        if not self.unarchive_card():
            return None
        return solve_info

    def unarchive_card(self) -> bool:
        overflow_btn = self.device.xpath(xpath_consts.OVERFLOW_BTN)
        if not overflow_btn.exists:
            return False

        overflow_btn.click(timeout=timer_consts.CLICK_TIMEOUT)
        time.sleep(0.5)
        unarchive_btn = self.device.xpath(xpath_consts.UNARCHIVE_BTN)
        if not unarchive_btn.exists:
            return False

        unarchive_btn.click(timeout=timer_consts.CLICK_TIMEOUT)
        return True

    def get_solve_info(self) -> Optional[SolveInfo]:
        try:
            d = self.device
            time = d.xpath(xpath_consts.TIME_TEXT).get_text()
            date = d.xpath(xpath_consts.DATE_TEXT).get_text()
            if time is None or date is None:
                return None
            scramble = d.xpath(xpath_consts.SCRAMBLE_TEXT).get_text()
            comment = self.device.xpath(xpath_consts.COMMENT_TEXT)
            comment = comment.get_text() if comment.exists else None
            penalty = self.device.xpath(xpath_consts.PENALTY_TEXT)
            penalty = penalty.get_text() if penalty.exists else None
            return SolveInfo(self.puzzle_type.value, self.group_name, time, date, scramble, comment, penalty)
        except RuntimeError:
            self.device.screenshot()
            logger.error(traceback)
            return None

    def click_first_card_info(self) -> bool:
        if self.x1 is None or self.y1 is None:
            (x, y) = self.device.xpath(xpath_consts.FIRST_DATA_CARD_ITEM).get().center()
            self.x1 = x
            self.y1 = y
        self.device.click(self.x1, self.y1)
        return True

    def click_history_btn(self) -> bool:
        self.device.xpath(xpath_consts.HISTORY_BTN).click(timeout=timer_consts.CLICK_TIMEOUT)
        return True

    def is_card_showed(self) -> bool:
        return self.device.xpath(xpath_consts.COMMENT_BTN).exists

    def has_data_card(self) -> bool:
        if not self.is_data_page():
            return False

        return self.device.xpath(xpath_consts.DATA_CARD_ITEM).exists

    def is_data_page(self) -> bool:
        if not self.is_main_page():
            return False

        return self.device.xpath(xpath_consts.SEARCH_BOX).exists


class AutoOutputer:
    def __init__(self, file_path: str = 'output_tmp.txt', puzzle_type: PuzzleType = PuzzleType.RUBIK_3, group_name: str = 'Normal'):
        device = u2.connect()
        if device is None:
            raise RuntimeError
        data_page = _DataPage(device, puzzle_type, group_name)
        self.data_page = data_page
        if data_page.is_twisty_running():
            data_page.twisty_stop()
        data_page.twisty_start()
        self.solve_info_data = []
        self.file_path = file_path

    def output_cur_archive(self):
        if not self.data_page.is_data_page():
            self.data_page.switch_to_data()
        self.data_page.click_history_btn()

        with open(self.file_path, 'a') as file:
            while True:
                try:
                    solve_info = self.data_page.opration_on_first_card()
                    if solve_info is None:
                        break
                    insert = solve_info.get_insert_string()
                    file.write(insert + '\n')
                    logger.info('[Write to file] {' + insert + '}')
                    global exit_flag
                    if exit_flag:
                        logger.info('[Exit] exit due to keyboard input')
                        return
                except XPathElementNotFoundError as err:
                    print(err.__traceback__)
                finally:
                    time.sleep(0.5)


def command_line():
    global exit_flag
    tmp = stdin.readline()
    if tmp is not None and tmp != '':
        exit_flag = True


def init_logger():
    logging.basicConfig(filename='../log/auto_outputer.log',
                        filemode='w',
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)s - %(message)s')
    global logger
    logger = logging.getLogger('AutoOutputer')
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler('../log/auto_outputer.log', mode='w', encoding='utf-8')
    fmt = logging.Formatter(fmt='%(asctime)s - %(levelname)s : %(message)s')
    console_handler.setFormatter(fmt)
    file_handler.setFormatter(fmt)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def main():
    init_logger()
    main_thread = Thread(target=AutoOutputer().output_cur_archive())
    input_thread = Thread(target=command_line())
    input_thread.start()
    main_thread.start()


if __name__ == '__main__':
    main()
