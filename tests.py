import random
import unittest
from storage import menu
from main import settings, LunchOrderBot

class LunchbotTest(unittest.TestCase):

    def setUp(self):
        self.bot = LunchOrderBot(
            'lunch.sqlite',
            channels=getattr(settings, 'channels', [])
        )

    def test_getrandom(self):
        self.assertEqual(len(menu.getrandombyprice()), 1)

if __name__ == '__main__':
    unittest.main()
