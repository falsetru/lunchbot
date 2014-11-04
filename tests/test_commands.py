# coding: utf-8

import collections

import mock
import pytest

from main import Command, Order, IdNameMap


@pytest.fixture
def cmd(request):
    ret = Command()
    ret.send_text = mock.Mock()
    ret.subscribe = mock.Mock()
    ret.unsubscribe = mock.Mock()
    ret.channels = {'#interesting_channel'}
    ret.orders = collections.defaultdict(Order)
    ret.names = IdNameMap({'a': 'a-fullname', 'b': 'b-fullname'})
    return ret


def gen_msg(msg, **kwargs):
    kwargs['FromHandle'] = kwargs.pop('FromHandle', 'a')
    kwargs['Sender.FullName'] = kwargs.pop('FullName', 'a-fullname')
    kwargs['ChatName'] = kwargs.pop('ChatName', '#current_channel')
    ret = mock.Mock()
    ret.configure_mock(
        Body=msg,
        **kwargs
    )
    return ret


def in_(cmd, msg_body, **kwargs):
    msg = gen_msg(msg_body, **kwargs)
    cmd.handle_msg(msg)
    return msg


def out(cmd, want):
    cmd.send_text.assert_called_with(mock.ANY, want)


def no_out(cmd):
    assert not cmd.send_text.called


def get_output(cmd):
    return cmd.send_text.call_args[0][1]


# ----------------------------------------------------------------------


def test_ping(cmd):
    in_(cmd, '!ping')
    out(cmd, 'pong')


def test_whereami(cmd):
    in_(cmd, '!whereami')
    out(cmd, '#current_channel')


def test_summon(cmd):
    in_(cmd, '!summon')
    cmd.subscribe.assert_called_with('#current_channel')


def test_dismiss(cmd):
    in_(cmd, '!dismiss')
    cmd.unsubscribe.assert_called_with('#current_channel')


def test_hello(cmd):
    in_(cmd, '!hello')
    out(cmd, mock.ANY)


def test_remember_id_names(cmd):
    in_(cmd, '!hello', FromHandle='someid', FullName='full name')
    cmd.names['someid'] == 'full name'
