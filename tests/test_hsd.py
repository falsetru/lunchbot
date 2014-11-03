# coding: utf-8

import hsd
from .utils import read_fixture, use_net_resource


def test_parse_menus():
    html = read_fixture('hsd-lunch-20141016.html')
    menus = list(hsd.parse_menus(html))
    assert len(menus) == 75
    assert (u'고기고기반찬', '2900') in menus
    assert (u'단호박샐러드', '1500') in menus


@use_net_resource
def test_get_menus():
    menus = list(hsd.get_menus())
    assert menus
    assert all(name and value.isdigit() for name, value in menus)
