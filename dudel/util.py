# -*- coding: utf-8 -*-

from dudel import default_timezone
import re, random, pytz
from enum import Enum

class PollExpiredException(Exception):
    def __init__(self, poll):
        self.poll = poll

class PollActionException(Exception):
    def __init__(self, poll, action):
        self.poll = poll
        self.action = action

class LocalizationContext(object):
    def __init__(self, user, poll):
        self.user = user
        self.poll = poll

    @property
    def timezone(self):
        # If the poll has a timezone set, always use the poll's timezone
        if self.poll and self.poll.timezone:
            return self.poll.timezone

        # If there is a user, use that user's timezone
        if self.user and self.user.is_authenticated():
            return self.user.timezone

        # Use the default timezone for unauthenticated users, or contexts without a user
        return default_timezone

    def utc_to_local(self, datetime):
        if not datetime: return None
        return pytz.utc.localize(datetime).astimezone(self.timezone)

    def local_to_utc(self, datetime):
        if not datetime: return None
        return self.timezone.localize(datetime).astimezone(pytz.utc).replace(tzinfo=None)

class DateTimePart(str, Enum):
    date = "date"
    time = "time"
    datetime = "datetime"

class PartialDateTime(object):
    def __init__(self, datetime, part, localization_context=None):
        self.datetime = datetime
        self.part = part
        self.localization_context = localization_context

    def __lt__(self, other):
        return self.datetime < other.datetime

    def __eq__(self, other):
        return isinstance(other, PartialDateTime) and self.part == other.part and self.format() == other.format()

    def format(self):
        from dudel.filters import date, time, datetime
        if self.part == DateTimePart.date:
            return date(self.datetime, ref=self.localization_context)
        elif self.part == DateTimePart.time:
            return time(self.datetime, ref=self.localization_context)
        elif self.part == DateTimePart.datetime:
            return datetime(self.datetime, ref=self.localization_context)


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
