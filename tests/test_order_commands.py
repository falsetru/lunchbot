# coding: utf-8

import mock
import pytest

from .test_commands import cmd
from .test_commands import in_, out, no_out


@pytest.fixture
def menus(request):
    tbl = {
        u'고기고기도시락': 3000,
        u'해피박스': 1000,
    }

    def get(self, name):
        price = tbl.get(name)
        if not price:
            return
        return name, price
    patcher = mock.patch('storage.Menu.get', get)
    patcher.start()
    request.addfinalizer(patcher.stop)


def test_orders_response_with_ordered_menu_summary(cmd, menus):
    in_(cmd, u'고기고기도시락')
    out(cmd, cmd.orders['a'].summary())


def test_an_order(cmd, menus):
    in_(cmd, u'고기고기도시락')
    assert cmd.orders['a'].menus == {u'고기고기도시락': 1}


def test_order_accumulation(cmd, menus):
    in_(cmd, u'고기고기도시락')
    in_(cmd, u'고기고기도시락')
    assert cmd.orders['a'].menus == {u'고기고기도시락': 2}


def test_order_with_quantity(cmd, menus):
    in_(cmd, u'고기고기도시락 x 4')
    assert cmd.orders['a'].menus == {u'고기고기도시락': 4}


def test_order_multiple_menus(cmd, menus):
    in_(cmd, u'고기고기도시락, 해피박스')
    assert cmd.orders['a'].menus == {u'고기고기도시락': 1, u'해피박스': 1}


def test_order_with_unknown_menu(cmd, menus):
    in_(cmd, u'개구리반찬')
    assert not cmd.orders
    no_out(cmd)


def test_metoo(cmd, menus):
    in_(cmd, u'고기고기도시락')
    in_(cmd, u'!metoo', FromHandle='b')
    out(cmd, cmd.orders['b'].summary())
    assert cmd.orders['b'] == cmd.orders['a']
