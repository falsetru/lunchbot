# coding: utf-8

import pytest

from data_structures import IdNameMap


@pytest.fixture
def names():
    names = IdNameMap()
    names.add(u'jmlee', u'Jeong-Min')
    names.add(u'robert', u'Robert Jerovsek')
    names.add(u'hyunmin', u'현민')
    return names


def test_find_exact_match(names):
    assert names.find(u'Jeong-Min') == u'jmlee'
    assert names.find(u'jmlee') == u'jmlee'
    assert names.find(u'robert') == u'robert'
    assert names.find(u'robert') == u'robert'


def test_find_partial_match(names):
    assert names.find(u'jerovsek') == u'robert'
    assert names.find(u'Robert') == u'robert'
    assert names.find(u'최현민') == u'hyunmin'
