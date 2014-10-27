import mock
import pytest

from main import Command


@pytest.fixture
def cmd(request):
    ret = Command()
    ret.send_text = mock.Mock()
    ret.channels = {'#interesting_channel'}
    return ret


@pytest.fixture
def msg():
    return mock.Mock()


def test_ping(cmd, msg):
    cmd._handle_ping(msg)
    cmd.send_text.assert_called_with(msg, 'pong')


# XXX
def test_summon(cmd, msg):
    msg.ChatName = '#current_channel'
    cmd._handle_summon(msg)
    assert cmd.channels == {'#interesting_channel', '#current_channel'}


# XXX
def test_dismiss(cmd, msg):
    msg.ChatName = '#interesting_channel'
    cmd._handle_dismiss(msg)
    assert cmd.channels == set()
