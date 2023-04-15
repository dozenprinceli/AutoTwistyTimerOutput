import time
import traceback
from enum import Enum, unique
from typing import Optional

from uiautomator2 import Device

from twistytimer.utils import xpath_consts, timer_consts, data_utils
from twistytimer.utils.timer_consts import *


@unique
class _MainTab(Enum):
    TIMER = 0
    DATA = 1
    STATISTICS = 2


class SolveInfo:
    def __init__(self, time: str, date: str, scramble: str, comment: str, penalty: str):
        self.time = data_utils.convert_time_str(time)
        self.date = data_utils.convert_date_str(date)
        self.scramble = scramble or ''
        self.penalty = penalty or '0'
        self.comment = comment or ''

    def __repr__(self):
        return 'time: ' + str(self.time) + ', date: ' + str(self.date) + ', scramble: ' + self.scramble \
               + ', penalty: ' + self.penalty + ', comment: ' + self.comment

    def get_insert_string(self):
        return '"' + str(self.time) + '";"' + str(self.date) + '";"' + self.scramble + '";"' + self.penalty \
               + '";"' + self.comment + '"'


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
            print('Current App: ' + self.device.app_info(timer_consts.TWISTY_TIMER_APP))
        return success

    def is_twisty_running(self) -> bool:
        if not self.is_device_running():
            return False

        try:
            app_info = self.device.app_current()
            package = app_info['package']
            return package == timer_consts.TWISTY_TIMER_APP
        except OSError:
            traceback.print_exc()
            return False

    def is_device_running(self) -> bool:
        return self.device is not None


class _DataPage(_TwistyTimer):
    def __init__(self, device: Device):
        super().__init__(device)

    def opration_on_first_card(self) -> Optional[SolveInfo]:
        if not self.click_first_card_info():
            return None
        solve_info = self.get_solve_info()
        if solve_info is None:
            return None
        if not self.unarchive_card():
            return None
        return solve_info

    def unarchive_card(self) -> bool:
        if not self.is_card_showed():
            return False

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
        if not self.is_card_showed():
            return None

        try:
            d = self.device
            time = d.xpath(xpath_consts.TIME_TEXT).get_text()
            date = d.xpath(xpath_consts.DATE_TEXT).get_text()
            scramble = d.xpath(xpath_consts.SCRAMBLE_TEXT).get_text()
            comment = self.device.xpath(xpath_consts.COMMENT_TEXT)
            comment = comment.get_text() if comment.exists else None
            penalty = self.device.xpath(xpath_consts.PENALTY_TEXT)
            penalty = penalty.get_text() if penalty.exists else None
            return SolveInfo(time, date, scramble, comment, penalty)
        except RuntimeError:
            self.device.screenshot()
            traceback.print_exc()
            return None

    def click_first_card_info(self) -> bool:
        if not self.has_data_card():
            return False

        self.device.xpath(xpath_consts.FIRST_DATA_CARD_ITEM).click(timeout=CLICK_TIMEOUT)
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
