# coding: utf-8

import urllib
import contextlib
import lxml.html


def get_menus():
    url = 'http://www.hsd.co.kr/lunch/lunchList.html'
    with contextlib.closing(urllib.urlopen(url)) as u:
        html = u.read()
    return parse_menus(html)


def parse_menus(html):
    root = lxml.html.fromstring(html)
    for name in root.cssselect('#cont_detail_area .product_copy01'):
        price, = name.getparent().cssselect('.product_price01')
        name = name.text_content().strip()
        price = price.text_content().strip().strip(u'원').replace(',', '')
        yield name, price


if __name__ == '__main__':
    for name, price in get_menus():
        print name, price
