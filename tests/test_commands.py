import pytest

from main import LunchOrderBot


@pytest.fixture
def bot(monkeypatch):
    monkeypatch.setattr(
        LunchOrderBot,
        'attach',
        lambda self: None
    )
    monkeypatch.setattr(
        LunchOrderBot,
        'send_text',
        lambda self, msg, text: setattr(bot, '_last_msg', text)
    )
    bot = LunchOrderBot(':memoery', [])
    return bot


@pytest.fixture
def msg():
    return object()


def test_ping(bot, msg):
    bot._handle_ping(msg)
    assert bot._last_msg == 'pong'
