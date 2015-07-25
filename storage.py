#!/usr/bin/env python
# coding: utf-8

import contextlib
import importlib
import json
import sqlite3
import sys


@contextlib.contextmanager
def conn(path):
    db = sqlite3.connect(path)
    try:
        yield db
    finally:
        db.close()


def setup_db(path):
    with conn(path) as db:
        db.execute(u'''
        CREATE TABLE IF NOT EXISTS menu (
            name TEXT PRIMARY KEY,
            price INT,
            restaurant TEXT
        )''')
        db.execute(u'''
        CREATE TABLE IF NOT EXISTS order_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle TEXT,
            fullname TEXT,
            items TEXT,
            total INT,
            timestamp NUM
        )''')
        db.commit()
        db.close()
    return lambda: conn(path)


class Connect(object):

    def __init__(self, connect):
        self.connect = connect


class Menu(Connect):

    def populate(self, restaurant, menus):
        with self.connect() as db:
            db.execute(
                u'DELETE FROM menu WHERE restaurant = ?',
                [restaurant])
            for name, price in menus:
                ok = True
                try:
                    db.execute(
                        u'INSERT INTO menu(name, price, restaurant) '
                        u'VALUES(?, ?, ?)',
                        (name.replace(' ', ''), price, restaurant))
                except sqlite3.Error as e:
                    ok = False
                print name, price
                if not ok:
                    print '!!!!', e
            db.commit()
            db.close()

    def get(self, name):
        with self.connect() as db:
            rows = list(db.execute(
                u'''SELECT name, price, restaurant
                FROM menu WHERE name = ?''',
                [name]))
            if len(rows) == 1:
                return rows[0]
            rows = list(db.execute(
                u'''SELECT name, price, restaurant
                FROM menu WHERE name LIKE ?''',
                [u'%{}%'.format(name)]))
            if len(rows) == 1:
                return rows[0]

    def getall(self, restaurant=None):
        with self.connect() as db:
            if restaurant:
                where = 'WHERE restaurant = ?'
                args = (restaurant,)
            else:
                where = ''
                args = ()
            sql = (
                u'SELECT name, price FROM menu {} ORDER BY price DESC'
                .format(where)
            )
            return list(db.execute(sql, args))

    def getrandombyprice(self, min=1000, max=5000):
        with self.connect() as db:
            rows = list(db.execute(
                u'SELECT name, price FROM menu WHERE price between ? and ? '
                u'ORDER BY RANDOM() LIMIT 1', [min, max]))
            return rows[0]


class OrderRecord(Connect):

    def add(self, handle, fullname, items, total, timestamp):
        with self.connect() as db:
            sql = u'''
                INSERT INTO order_record
                (handle, fullname, items, total, timestamp)
                VALUES (?, ?, ?, ?, ?)
            '''
            db.execute(sql, [
                handle,
                fullname,
                json.dumps(items, ensure_ascii=False),
                total,
                timestamp
            ])
            db.commit()

    def get_last_order(self, handle, offset):
        with self.connect() as db:
            sql = u'''
                SELECT items FROM order_record WHERE handle = ?
                ORDER BY id DESC LIMIT 1 OFFSET ?
            '''
            rows = list(db.execute(sql, [handle, offset]))
            return rows[0][0] if rows else None

    def get_recent_orders(self, handle):
        with self.connect() as db:
            sql = u'''
                SELECT items, total, timestamp
                FROM order_record WHERE handle = ?
                ORDER BY id DESC LIMIT 20
            '''
            return list(db.execute(sql, [handle]))


db = setup_db('lunch.sqlite')
menu = Menu(db)
order_record = OrderRecord(db)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        module_names = sys.argv[1:]
    else:
        module_names = ['hsd', 'mcdonalds', 'burgerking']
    for module_name in module_names:
        mod = importlib.import_module(module_name)
        menu.populate(module_name, mod.get_menus())
