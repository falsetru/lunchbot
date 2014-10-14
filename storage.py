#!/usr/bin/env python
# coding: utf-8

import contextlib

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
        CREATE TABLE IF NOT EXISTS message (
            id INT PRIMARY KEY,
            handle TEXT,
            fullname TEXT,
            body TEXT,
            timestamp NUM

        )''')
        db.commit()
        db.close()
    return lambda: conn(path)


class Menu(object):

    def __init__(self, connect):
        self.connect = connect

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
                u'SELECT name, price FROM menu WHERE name LIKE ?', [u'%{}%'.format(name)]))
            if len(rows) == 1:
                return rows[0]



class Message(object):
    def __init__(self, db):
        self.connect = connect

db = setup_db('lunch.sqlite')
menu = Menu(db)

if __name__ == '__main__':
    import importlib
    hsd = importlib.import_module('hsd')
    menu.populate(hsd.get_menus())
    #print u'{} {}'.format(*menu.get(u'고기고기반찬'))
    #print u'{} {}'.format(*menu.get(u'참치야채'))
