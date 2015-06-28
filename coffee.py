# coding: utf-8

import csv
import os


def get_menus():
    filepath = os.environ.get('COFFEE_PATH', 'coffee.txt')
    with open(filepath) as f:
        reader = csv.reader(f)
        for name, price in reader:
            yield name.decode('utf-8'), price.replace(',', '').decode('utf-8')


if __name__ == '__main__':
    for name, price in get_menus():
        print name, price
