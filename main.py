#!/usr/bin/env python
# coding: utf-8

import collections
import datetime
import json
import random
import re
import time

import Skype4Py

from data_structures import CappedSet, IdNameMap
from storage import menu, order_record
try:
    import settings
except ImportError:
    settings = object()
rand = random.SystemRandom()


class Order(object):

    def __init__(self):
        self.clear()

    def __eq__(self, other):
        return self.menus == other.menus

    def add(self, name, price, qty=1):
        self.menus[name] += qty
        self.total += price * qty

    def clear(self):
        self.menus = collections.Counter()
        self.total = 0

    def populate(self, menus):
        self.menus = collections.Counter(menus)
        self.total = sum(
            menu.get(name)[1] * qty for name, qty in menus.items()
        )
        return self

    def copy(self):
        c = Order()
        c.menus = self.menus.copy()
        c.total = self.total
        return c

    def summary(self):
        return u'{} = {:,}'.format(
            u' + '.join(
                u'{} x {}'.format(name, qty)
                for name, qty in self.menus.items()
            ),
            self.total
        )


class Command(object):

    cmd_pattern = re.compile(ur'^!([a-z_\d]+)\b', flags=re.IGNORECASE)
    qty_pattern = re.compile(ur'^(?P<name>.*)\s*[x*]\s*(?P<qty>\d+)\s*$',
                             flags=re.IGNORECASE | re.UNICODE)
    sep_pattern = re.compile(ur'[.,;+/]|\band\b',
                             flags=re.IGNORECASE | re.UNICODE)
    redundant_chars = re.compile(ur'[ ®™]')
    menu_urls = (
        u'한솥 - http://www.hsd.co.kr/lunch/lunchList.html\n'
        u'버거왕 - https://delivery.burgerking.co.kr/menu/all\n'
        u'MC도날드 - https://www.mcdelivery.co.kr/kr/browse'
        u'/menu.html?daypartId=1&catId=11\n'
    )

    def handle_msg(self, msg):
        self.names.add(msg.FromHandle, msg.Sender.FullName)
        self.handle_order(msg) or self.handle_misc(msg)

    def handle_order(self, msg):
        any_order = False
        for item in self.sep_pattern.split(msg.Body):
            matched = self.qty_pattern.match(item.strip())
            if matched:
                name, qty = matched.group('name'), int(matched.group('qty'))
            else:
                name, qty = item, 1
            name = self.redundant_chars.sub(u'', name)
            name_price = menu.get(name)
            if not name_price:
                continue
            any_order = True
            name, price, restaurant = name_price
            o = self.orders[msg.FromHandle]
            o.add(name, price, qty=qty)
        if any_order:
            self.send_text(msg, o.summary())
            self.last_orderer = msg.FromHandle
        return any_order

    def handle_misc(self, msg):
        matched = self.cmd_pattern.match(msg.Body.strip())
        if not matched:
            return
        cmd = matched.group(1)
        attr = getattr(self, '_handle_{}'.format(cmd.lower()), None)
        if callable(attr):
            attr(msg)

    def _handle_metoo(self, msg):
        id_ = self.last_orderer
        xs = msg.Body.split()
        if len(xs) > 1:
            candidate = self.names.find(xs[1])
            if candidate:
                id_ = candidate
        if id_ not in self.orders:
            return
        o = self.orders[msg.FromHandle] = self.orders[id_].copy()
        self.send_text(msg, u'Same as {}: {}'.format(
            self.names[id_], o.summary())
        )

    def _handle_hello(self, msg):
        self.send_text(
            msg,
            u'점심봇 (experimental): '
            u'한솥 도시락 / 햄버거 을 드실분은 알려주세요. '
            u'현민님이 주문 대행해 드립니다.\n' +
            self.menu_urls +
            u', '.join('!{}'.format(
                x.split('_', 2)[-1])
                for x in dir(self) if x.startswith('_handle')
            )
        )

    _handle_help = _handle_hello

    def _handle_clear(self, msg):
        self.orders.pop(msg.FromHandle, None)
        self.send_text(msg, u'{0.FullName} ({0.Handle}): OUT'.format(
            msg.Sender
        ))

    def _handle_clearall(self, msg):
        self.orders.clear()
        self.send_text(msg, u'EMPTY')

    def _handle_sum(self, msg):
        if not self.orders:
            self.send_text(msg, u'읭? No order at all.')
            return

        text = []
        for restaurant, orders in self.group_by_restaurant().items():
            text += self._sum_for_a_restaurant(restaurant, orders)
        self.send_text(msg, u'\n'.join(text))

    def _sum_for_a_restaurant(self, restaurant, orders):
        text = []
        text.append(u' Menu - {} '.format(restaurant).center(80, u'-'))
        cnt = collections.Counter()
        for o in orders.values():
            cnt += o.menus
        for name, c in cnt.most_common():
            text.append(u'{} x {}'.format(name, c))
        text.append(u' Show me the money '.center(80, u'-'))
        for handle, o in orders.items():
            text.append(u'{} ({}): {}'.format(
                self.names[handle],
                handle,
                o.summary()
            ))
        text.append(
            u'Total: {:,}'.format(
                sum(o.total for o in orders.values())
            )
        )
        return text

    def group_by_restaurant(self):
        result = collections.defaultdict(
            lambda: collections.defaultdict(Order)
        )
        for handle, order in self.orders.items():
            for name, qty in order.menus.items():
                name, price, restaurant = menu.get(name)
                result[restaurant][handle].add(
                    name, int(price), qty
                )
        return result

    def _handle_menu(self, msg):
        self.send_text(msg, self.menu_urls)

    def _handle_hello_coffeebot(self, msg):
        txt = u'\n'.join(
            u'{} - {}'.format(name, price) for name, price in
            menu.getall(restaurant='coffee')
        )
        self.send_text(msg, txt)

    def _handle_fin(self, msg):
        if not self.orders:
            self.send_text(msg, u'No order')
            return
        timestamp = time.time()
        for handle, o in self.orders.items():
            order_record.add(
                handle, self.names[handle], dict(o.menus),
                o.total, timestamp
            )

        handles = set()
        for handle, order in self.orders.items():
            for m in order.menus:
                _, _, restaurant = menu.get(m)
                if restaurant == 'hsd':
                    handles.add(handle)
        if handles:
            deliverer = rand.choice(list(handles))
            self.send_text(msg, u'{}({}) 님 고고!'.format(
                self.names[deliverer],
                deliverer
            ))

    def _handle_ping(self, msg):
        self.send_text(msg, u'pong')

    def _handle_summon(self, msg):
        self.subscribe(msg.ChatName)

    def _handle_dismiss(self, msg):
        self.unsubscribe(msg.ChatName)

    def _handle_whereami(self, msg):
        self.send_text(msg, msg.ChatName)

    def _handle_salt(self, msg):
        "Same as last time"
        try:
            offset = int(msg.Body.split()[1])
        except (IndexError, ValueError):
            offset = 0
        o = order_record.get_last_order(msg.FromHandle, offset)
        if not o:
            self.send_text(msg, u'No order')
            return
        items = json.loads(o)
        self.send_text(
            msg,
            self.orders[msg.FromHandle].populate(items).summary()
        )

    def _handle_recent_orders(self, msg):
        def _():
            for i, (items, total, timestamp) in enumerate(records):
                dt = datetime.datetime.fromtimestamp(timestamp)
                items = json.loads(items)
                yield u'{}. {:%Y-%m-%d} : {} = {:,}'.format(
                    i, dt,
                    u' + '.join(u'{} x {}'.format(name, cnt)
                                for name, cnt in items.items()),
                    total
                )
        records = order_record.get_recent_orders(msg.FromHandle)
        txt = u'\n'.join(reversed(list(_())))
        self.send_text(msg, txt or u'No order')

    def _handle_random(self, msg):
        name_price = menu.getrandombyprice()
        o = self.orders[msg.FromHandle]
        o.add(*name_price)
        self.send_text(msg, o.summary())
        self.last_orderer = msg.FromHandle

    def _handle_pick(self, msg):
        try:
            n = int(msg.Body.split()[1])
            if n <= 0:
                raise ValueError()
        except (IndexError, ValueError):
            n = 1
        try:
            people = [
                u'{} ({})'.format(p.FullName, p.Handle)
                for p in msg.Chat.Members
            ]
            people = rand.sample(people, n)
        except ValueError as e:
            self.send_text(msg, str(e))
        else:
            self.send_text(
                msg,
                u'\n'.join(people)
            )


class LunchOrderBot(Command):

    def __init__(self, sqlite_path, channels):
        self.sqlite_path = sqlite_path
        self.channels = set(channels)
        self.names = IdNameMap()
        self.last_orderer = None
        self.seen = CappedSet(maxlen=1024)
        self.orders = collections.defaultdict(Order)
        self.skype = Skype4Py.Skype(Events=self)
        self.skype.Attach()

    def MessageStatus(self, msg, status):
        if msg.ChatName not in self.channels:
            if msg.Body not in ('!summon', '!whereami'):
                return
        if status in (Skype4Py.cmsReceived,
                      Skype4Py.cmsSent,
                      Skype4Py.cmsSending):
            if status == Skype4Py.cmsReceived:
                msg.MarkAsSeen()
            elif msg.Id in self.seen:
                return

            self.handle_msg(msg)
            self.seen.add(msg.Id)

    def send_text(self, msg, text):
        sent = msg.Chat.SendMessage(text)
        self.seen.add(sent.Id)

    def subscribe(self, channel):
        self.channels.add(channel)

    def unsubscribe(self, channel):
        self.channels.remove(channel)


if __name__ == "__main__":
    bot = LunchOrderBot(
        'lunch.sqlite',
        channels=getattr(settings, 'channels', [])
    )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
