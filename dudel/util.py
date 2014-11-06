class PollExpiredException(Exception):
    def __init__(self, poll):
        self.poll = poll

class PollActionException(Exception):
    def __init__(self, poll, action):
        self.poll = poll
        self.action = action

def load_icons(filename):
    with open(filename) as f:
        lines = f.readlines()
        return [x.strip("\n").split(" ", 1) for x in lines if x]
    return []
