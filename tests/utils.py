import os

import pytest


def read_fixture(path):
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'fixtures',
        path
    )
    with open(path, 'rb') as f:
        return f.read()

use_net_resource = pytest.mark.skipif(
    not os.environ.get('USE_NET_RESOURCE', 0),
    reason='require network resource'
)
