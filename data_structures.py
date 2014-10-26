import collections


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

