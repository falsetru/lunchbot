# coding: utf-8

import burgerking
from .utils import read_fixture, use_net_resource


def test_parse_menus():
    json_string = read_fixture('burgerking-20141123.json')
    menus = list(burgerking.parse_menus(json_string))
    assert len(menus) == 88
    assert (u'치폴레 팩(치킨)', '15700') in menus
    assert (u'와퍼세트', '7600') in menus
    assert (u'오렌지에이드', '2600') in menus


@use_net_resource
def test_get_menus():
    menus = list(burgerking.get_menus())
    assert menus
    assert all(name and value.isdigit() for name, value in menus)
