# coding: utf-8

import contextlib
import urllib

import lxml.html


def get_menus():
    url = ('https://www.mcdelivery.co.kr/kr/browse/menu.html'
           '?daypartId=1&catId=11')
    with contextlib.closing(urllib.urlopen(url)) as u:
        html = u.read()
    return parse_menus(html)


def parse_menus(html):
    root = lxml.html.fromstring(html)
    for panel in root.cssselect('#product-cards .panel-product'):
        name, = panel.cssselect('.product-title')
        price, = panel.cssselect('.starting-price')
        yield name.text, ''.join(c for c in price.text if c.isdigit())


if __name__ == '__main__':
    for name, price in get_menus():
        print name, price
