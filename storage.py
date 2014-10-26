#!/usr/bin/env python
# coding: utf-8

import contextlib
import json
import sqlite3


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
            price INT
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

    def populate(self, menus):
        with self.connect() as db:
            db.execute(u'DELETE FROM menu')
            db.executemany(
                u'INSERT INTO menu(name, price) VALUES(?, ?)',
                [(name.replace(' ', ''), price) for name, price in menus])
            db.commit()
            db.close()

    def get(self, name):
        with self.connect() as db:
            rows = list(db.execute(
                u'SELECT name, price FROM menu WHERE name = ?', [name]))
            if len(rows) == 1:
                return rows[0]
            rows = list(db.execute(
                u'SELECT name, price FROM menu WHERE name LIKE ?',
                [u'%{}%'.format(name)]))
            if len(rows) == 1:
                return rows[0]

    def getall(self):
        with self.connect() as db:
            return list(db.execute(
                u'SELECT name, price FROM menu ORDER BY price DESC'
            ))

    def getrandombyprice(self, min=1000, max=5000):
        with self.connect() as db:
            rows = list(db.execute(
                u'SELECT name FROM menu WHERE price between ? and ? \
                ORDER BY RANDOM() LIMIT 1',   [min, max]
                ))
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
    import importlib
    hsd = importlib.import_module('hsd')
    menu.populate(hsd.get_menus())
