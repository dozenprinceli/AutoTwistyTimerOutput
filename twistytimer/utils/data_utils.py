import time


def convert_time_str(time_str: str) -> int:
    millis = 0
    rest = time_str
    if time_str.__contains__('h '):
        split = time_str.split('h ')
        hour = split[0]
        millis += int(hour) * 3600 * 1000
        rest = split[1]
    if rest.__contains__(':'):
        split = rest.split(':')
        minute = split[0]
        millis += int(minute) * 60 * 1000
        rest = split[1]
    if rest.__contains__('.'):
        split = rest.split('.')
        second = split[0]
        centi = split[1]
        millis += int(second) * 1000 + int(centi) * 10
    return millis


def convert_date_str(date_str: str, lang_table: dict = None) -> int:
    split = date_str.split('\n')
    if len(split) != 2:
        return -1
    date_split = split[0].split(' ')
    time_str = split[1]
    if len(date_split) != 3:
        return -1
    if date_split[1].endswith('月'):
        date_split[1] = date_split[1].replace('月', '')
    else:
        if lang_table is None or lang_table[date_split[1]] is None:
            return -1
        else:
            date_split[1] = lang_table[date_split[1]]
    date_time = date_split[0] + '-' + date_split[1] + '-' + date_split[2] + ' ' + time_str
    s_t = time.strptime(date_time, '%d-%m-%Y %H:%M')
    timestamp = int(time.mktime(s_t))
    return timestamp
