import time

import uiautomator2 as u2

from twistytimer import _TwistyTimer, _DataPage


def judge_status():
    print(timer.is_main_page())


def switch_tab():
    print(timer.switch_to_data())
    time.sleep(0.5)
    print(timer.switch_to_statistics())
    time.sleep(0.5)
    print(timer.switch_to_timer())


def show_card():
    data_page.switch_to_data()
    info_list = []
    idx = 0
    while idx < 20:
        info = data_page.opration_on_first_card()
        if info is None:
            break
        info_list.append(info)
        idx += 1
    for info in info_list:
        print('"333";"Normal";' + info.get_insert_string() + '\n')


def main():
    show_card()
    return


device = u2.connect()
timer = _TwistyTimer(device)
data_page = _DataPage(device)

if __name__ == '__main__':
    main()
