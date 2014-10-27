import mock
import pytest

from main import Command


@pytest.fixture
def cmd(request):
    ret = Command()
    ret.send_text = mock.Mock()
    ret.subscribe = mock.Mock()
    ret.unsubscribe = mock.Mock()
    ret.channels = {'#interesting_channel'}
    return ret


def gen_msg(msg, chatname='#current_channel'):
    ret = mock.Mock()
    ret.configure_mock(Body=msg, ChatName=chatname)
    return ret


def in_(cmd, msg_body):
    msg = gen_msg(msg_body)
    cmd.handle_misc(msg)
    return msg


def out(cmd, want):
    cmd.send_text.assert_called_with(mock.ANY, want)


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
