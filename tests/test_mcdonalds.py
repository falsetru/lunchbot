# coding: utf-8

import mcdonalds
from .utils import read_fixture, use_net_resource


def test_parse_menus():
    html = read_fixture('mcdonalds-20141123.html')
    menus = list(mcdonalds.parse_menus(html))
    assert len(menus) == 19
    assert (u'디럭스 슈림프 버거', '4200') in menus
    assert (u'맥스파이시™ 치킨텐더 - 4조각', '6000') in menus


@use_net_resource
def test_get_menus():
    menus = list(mcdonalds.get_menus())
    assert menus
    assert all(name and value.isdigit() for name, value in menus)
