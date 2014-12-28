# -*- coding: utf-8 -*-

import re, random

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

def get_slug(s):
    s = s.lower()
    s = re.sub(r'[\s+]+', '-', s)
    s = re.sub(r'[^a-zA-Z0-9_-]+', '', s)
    s = re.sub(r'-+', '-', s)
    s = re.sub(r'(^\-*|\-*$)', '', s)
    return s

def random_string(length=8):
    chars = "ABCDEFGHJKLMNPQRTUVWXYZabcdefghjkmnpqrstuvwxyz0123456789"
    return "".join([random.choice(chars) for i in range(length)])
