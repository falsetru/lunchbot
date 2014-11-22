# coding: utf-8

import contextlib
import json
import urllib


def get_menus():
    url = 'https://delivery.burgerking.co.kr/getMenuList'
    post_data = urllib.urlencode({
        'class_id': '00000',
        'base_id': '',
        'more_count': '0',
    })
    with contextlib.closing(urllib.urlopen(url, post_data)) as u:
        json_string = u.read()
    return parse_menus(json_string)


def parse_menus(json_string):
    lst = json.loads(json_string)
    for x in lst:
        yield x['product_nm'], x['price_0']


if __name__ == '__main__':
    for name, price in get_menus():
        print name, price
