import os


def read_fixture(path):
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'fixtures',
        path
    )
    with open(path, 'rb') as f:
        return f.read()
