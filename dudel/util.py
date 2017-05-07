# -*- coding: utf-8 -*-

import random, re, pytz, enum

class DateTimePart(str, enum.Enum):
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
