# coding: utf-8

import json

import mock
import pytest

from .test_commands import cmd
from .test_commands import in_, out, no_out, get_output


assert callable(cmd)


@pytest.fixture
def menus(request):
    tbl = {
        u'고기고기도시락': 3000,
        u'해피박스': 1000,
    }
    mocks = {}

    def get(name):
        price = tbl.get(name)
        if not price:
            return
        return name, price

    def get_last_order(handle, idx):
        if idx == 0:
            return json.dumps({u'고기고기도시락': 1})
        else:
            return json.dumps({u'해피박스': 2})

    patcher = mock.patch('storage.Menu.get', side_effect=get)
    patcher.start()
    request.addfinalizer(patcher.stop)

    patcher = mock.patch('storage.OrderRecord.add')
    mocks['add'] = patcher.start()
    request.addfinalizer(patcher.stop)

    patcher = mock.patch(
        'storage.OrderRecord.get_last_order',
        side_effect=get_last_order)
    mocks['get_last_order'] = patcher.start()
    request.addfinalizer(patcher.stop)
    return mocks


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


def test_clear(cmd, menus):
    in_(cmd, u'고기고기도시락')
    in_(cmd, u'고기고기도시락', FromHandle='b')
    in_(cmd, u'!clear')
    assert 'a' not in cmd.orders
    assert cmd.orders['b'].menus == {u'고기고기도시락': 1}


def test_clearall(cmd, menus):
    in_(cmd, u'고기고기도시락')
    in_(cmd, u'고기고기도시락', FromHandle='b')
    in_(cmd, u'!clearall')
    assert not cmd.orders


def test_sum(cmd, menus):
    in_(cmd, u'고기고기도시락')
    in_(cmd, u'고기고기도시락', FromHandle='b')
    in_(cmd, u'!sum')
    got = get_output(cmd)
    assert u'고기고기도시락 x 2' in got
    assert u'a-fullname (a): 고기고기도시락 x 1 = 3,000' in got
    assert u'b-fullname (b): 고기고기도시락 x 1 = 3,000' in got
    assert u'Total: 6,000' in got


def test_fin(cmd, menus):
    in_(cmd, u'고기고기도시락')
    in_(cmd, u'고기고기도시락 x 2', FromHandle='b')
    in_(cmd, u'!fin')
    assert menus['add'].call_count == 2
    menus['add'].assert_has_calls([
        mock.call('a', 'a-fullname', {u'고기고기도시락': 1}, 3000, mock.ANY),
        mock.call('b', 'b-fullname', {u'고기고기도시락': 2}, 6000, mock.ANY)
    ])


def test_salt(cmd, menus):
    in_(cmd, u'!salt')
    assert cmd.orders['a'].menus == {u'고기고기도시락': 1}
    in_(cmd, u'!salt 0')
    assert cmd.orders['a'].menus == {u'고기고기도시락': 1}
    in_(cmd, u'!salt 1')
    assert cmd.orders['a'].menus == {u'해피박스': 2}
    assert menus['get_last_order'].call_count == 3
