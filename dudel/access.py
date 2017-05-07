def scope_matches(pattern, value):
    return pattern == value or pattern == '*'

HasScope = lambda scope: Has('scope', lambda s: scope_matches(scope, s))


class Has(object):
    def __init__(self, *args):
        self.data = args

    def test(self, *attribute):
        if len(attribute) != len(self.data):
            return False

        for test, value in zip(self.data, attribute):
            if test is ANY:
                continue

            if callable(test):
                if not test(value):
                    return False
            elif test != value:
                return False

        return True

    def matches(self, attributes):
        for attribute in attributes:
            if self.test(*attribute):
                return True
        return False

    def __call__(self, attributes):
        return self.matches(attributes)

    def __and__(self, other):
        return Every(self, other)

    def __or__(self, other):
        return Some(self, other)

class ANY(Has):
    def __init__(self):
        pass

    def test(self, *args):
        return True

    def matches(self, *args):
        return True

class Some(Has):
    def __init__(self, *children):
        self.children = children

    def matches(self, attributes):
        for child in self.children:
            if child.matches(attributes):
                return True
        return False

class Every(Has):
    def __init__(self, *children):
        self.children = children

    def matches(self, attributes):
        for child in self.children:
            if not child.matches(attributes):
                return False
        return True

class Not(Has):
    def __init__(self, child):
        self.child = child

    def matches(self, attributes):
        return not self.child.matches(attributes)


# Has('scope', 'self:read') and
# (Has('role', 'admin') or Has('user', user.id))
