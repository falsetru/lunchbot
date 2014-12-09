# coding: utf-8

import datetime
import json
import time

import mock
import pytest

from .test_commands import cmd
from .test_commands import in_, out, no_out, get_output


assert callable(cmd)


@pytest.fixture
def menus(request):
    tbl = {
        u'고기고기도시락': (3000, 'hsd'),
        u'해피박스': (1000, 'hsd'),
        u'빅맥': (2000, 'mcdonalds'),
    }
    mocks = {}

    def get(name):
        x = tbl.get(name)
        if not x:
            return
        price, restaurant = x
        return name, price, restaurant

    def getall():
        for menu in sorted(tbl):
            yield menu, tbl[menu][0]

    patcher = mock.patch('storage.Menu.get', side_effect=get)
    mocks['get'] = patcher.start()
    request.addfinalizer(patcher.stop)

    patcher = mock.patch('storage.Menu.getall', side_effect=getall)
    mocks['getall'] = patcher.start()
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
    got = get_output(cmd)
    assert 'Same as a-fullname' in got
    assert cmd.orders['b'].summary() in got
    assert cmd.orders['b'] == cmd.orders['a']


def test_metoo_with_others_name(cmd, menus):
    in_(cmd, u'해피박스', FromHandle=u'john', FullName=u'John Doe')
    in_(cmd, u'고기고기도시락', FromHandle=u'sam', FullName=u'Sam Ham')
    in_(cmd, u'!metoo john', FromHandle=u'b')
    got = get_output(cmd)
    assert 'Same as John Doe' in got
    assert cmd.orders['b'].summary() in got
    assert cmd.orders['b'] == cmd.orders['john']


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
    in_(cmd, u'고기고기도시락', FromHandle='b', FullName='b-fullname')
    in_(cmd, u'!sum')
    got = get_output(cmd)
    assert u'고기고기도시락 x 2' in got
    assert u'a-fullname (a): 고기고기도시락 x 1 = 3,000' in got
    assert u'b-fullname (b): 고기고기도시락 x 1 = 3,000' in got
    assert u'Total: 6,000' in got


def test_sum_group_by_restaurant(cmd, menus):
    in_(cmd, u'고기고기도시락')
    in_(cmd, u'빅맥', FromHandle='b', FullName='b-fullname')
    order_dicts = cmd.group_by_restaurant()
    assert isinstance(order_dicts, dict)
    assert set(order_dicts) == {'hsd', 'mcdonalds'}
    assert set(order_dicts['hsd']) == {'a'}
    assert set(order_dicts['mcdonalds']) == {'b'}

    in_(cmd, '!sum')
    got = get_output(cmd)
    assert u'고기고기도시락 x 1' in got
    assert u'빅맥 x 1' in got
    assert u'a-fullname (a): 고기고기도시락 x 1 = 3,000' in got
    assert u'b-fullname (b): 빅맥 x 1 = 2,000' in got
    assert u'Menu - hsd' in got
    assert u'Menu - mcdonalds' in got
    assert u'Total: 3,000' in got
    assert u'Total: 2,000' in got


def test_fin_without_order(cmd, menus):
    with mock.patch('storage.OrderRecord.add'):
        in_(cmd, u'!fin')
        out(cmd, u'No order')


def test_fin(cmd, menus):
    with mock.patch('storage.OrderRecord.add') as m:
        in_(cmd, u'고기고기도시락')
        in_(cmd, u'고기고기도시락 x 2', FromHandle='b')
        in_(cmd, u'!fin')
        assert m.call_count == 2
        m.assert_has_calls([
            mock.call('a', mock.ANY, {u'고기고기도시락': 1}, 3000, mock.ANY),
            mock.call('b', mock.ANY, {u'고기고기도시락': 2}, 6000, mock.ANY)
        ])


def test_fin_choose_deliverer(cmd, menus):
    with mock.patch('storage.OrderRecord.add'):
        in_(cmd, u'고기고기도시락')
        in_(cmd, u'고기고기도시락 x 2', FromHandle='b', FullName='b-fullname')
        in_(cmd, u'!fin')
        got = get_output(cmd)
        assert u'님 고고!' in got
        assert u'a-fullname(a)' in got or u'b-fullname(b)' in got


def test_salt(cmd, menus):
    def get_last_order(handle, idx):
        if idx == 0:
            return json.dumps({u'고기고기도시락': 1})
        else:
            return json.dumps({u'해피박스': 2})
    with mock.patch(
            'storage.OrderRecord.get_last_order',
            side_effect=get_last_order) as m:
        in_(cmd, u'!salt')
        assert cmd.orders['a'].menus == {u'고기고기도시락': 1}
        in_(cmd, u'!salt 0')
        assert cmd.orders['a'].menus == {u'고기고기도시락': 1}
        in_(cmd, u'!salt 1')
        assert cmd.orders['a'].menus == {u'해피박스': 2}
        assert m.call_count == 3


def test_menu(cmd, menus):
    in_(cmd, u'!menu')
    got = get_output(cmd)
    assert u'http://' in got


def test_recent_orders(cmd, menus):
    def t(y, m, d):
        return time.mktime(datetime.datetime(y, m, d).timetuple())
    with mock.patch('storage.OrderRecord.get_recent_orders', return_value=[]):
        in_(cmd, u'!recent_orders')
        out(cmd, u'No order')
    with mock.patch('storage.OrderRecord.get_recent_orders', return_value=[
            (json.dumps({'menu-a': '1'}), 1000, t(2014, 10, 30))]):
        in_(cmd, u'!recent_orders')
        out(cmd, u'0. 2014-10-30 : menu-a x 1 = 1,000')
    with mock.patch('storage.OrderRecord.get_recent_orders', return_value=[
            (json.dumps({'menu-a': 3, 'menu-b': '2'}), 5000, t(2014, 10, 30)),
            (json.dumps({'menu-a': '1'}), 1000, t(2014, 10, 20)),
    ]):
        in_(cmd, u'!recent_orders')
        out(cmd,
            u'1. 2014-10-20 : menu-a x 1 = 1,000\n'
            u'0. 2014-10-30 : menu-a x 3 + menu-b x 2 = 5,000')


def test_random(cmd, menus):
    with mock.patch(
            'storage.Menu.getrandombyprice',
            return_value=[u'고기고기도시락', 3000]):
        in_(cmd, u'!random')
        out(cmd, u'고기고기도시락 x 1 = 3,000')
    cmd.orders['a'].clear()
    with mock.patch(
            'storage.Menu.getrandombyprice',
            return_value=[u'해피박스', 1000]):
        in_(cmd, u'!random')
        out(cmd, u'해피박스 x 1 = 1,000')
