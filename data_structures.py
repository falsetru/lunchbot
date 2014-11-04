import collections
import difflib


class CappedSet(set):

    def __init__(self, maxlen):
        super(CappedSet, self).__init__()
        self.maxlen = maxlen
        self.q = collections.deque(maxlen=maxlen)

    def add(self, x):
        if x in self:
            return
        if len(self) >= self.maxlen:
            old = self.q.popleft()
            self.discard(old)
        super(CappedSet, self).add(x)
        self.q.append(x)


class IdNameMap(dict):

    def add(self, id_, name):
        self[id_] = name

    def find(self, id_or_name):
        d = {}
        for id_, name in self.iteritems():
            d[id_.lower()] = d[name.lower()] = id_
        m = difflib.get_close_matches(id_or_name, d, 1)
        if m:
            return d.get(m[0])
