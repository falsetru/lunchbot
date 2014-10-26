# coding: utf-8

import hsd
from .utils import read_fixture


def test_parse_menus():
    html = read_fixture('hsd-lunch-20141016.html')
    menus = list(hsd.parse_menus(html))
    assert len(menus) == 75
    assert (u'고기고기반찬', '2900') in menus
    assert (u'단호박샐러드', '1500') in menus
