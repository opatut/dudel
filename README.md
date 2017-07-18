# Warning! This project is deprecated.

I've been unable to maintain this project for some while now due to *not enough time*™. Some folks over at my university, where I also initially developed dudel, have taken the time to rewrite it using django, boosting the performance and generally improving the code base. A lot of dudel lives on in that new rewrite, [BitPoll](https://github.com/fsinfuhh/Bitpoll). Go check it out! :)

---

# Dudel

A simple group scheduling and poll tool, following the example of doodle.com and similar services.

## Setup

Make a virtual environment, activate it, run:

    pip install -r requirements.txt

This needs the development packages of some libraries, in particular: libpq, libldap, libsasl2.
Make sure you also have `scss` and `coffee` (from coffeescript) installed.

Copy `config.py.example` to `config.py` and adjust your settings.
You will probably want to change `DEBUG`, `TESTING` and `MAIL_DEBUG` for production environments!

    cp config.py.example config.py
    $EDITOR config.py

Create a test database:

    make seed

Create an empty database:

    make init

Compile the translations:

    make i18n-compile

Run the testserver:

    make run

## Migration

**WARNING!** While as a database backend all SQL-Alchemy supported databases
should work, migration is only available for PostgreSQL. This is due to complicated
upgrade tasks that require database-specific SQL commands, and me being too lazy to
implement many of them. For development, you probably want to use SQLite anyway and
throw away those databases all the time (`make seed`).

## Translating

Please translate. Run

    make i18n-update

then copy/edit translations files (in `dudel/translations`), then compile them with

    make i18n-compile

## Times

- ALL database times are UTC
- generated times are simply using datetime.utcnow()
- user-entered times are always converted from the user's Timezone
- Polls save the timezone of the user that created it
- Poll timezone can be changed, or set to "Transform to user's timezone"
- Poll view uses poll timezone, if it differs from user timezone, a warning is displayed
- Editing the poll's times uses the poll timezone, NOT the user's timezone

### Migration

- Convert user-entered times (due date, poll times) to UTC, assume they were default timezone
- Add timezone field to poll
- Add timezone field to user

## License

    Copyright (C) 2013 - 2015

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
