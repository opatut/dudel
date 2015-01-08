# Dudel

A simple group scheduling and poll tool, following the example of doodle.com and similar services.

## Setup

Make a virtual environment, activate it, run:

    pip install -r requirements.txt

Copy `config.py.example` to `config.py` and adjust your settings.

    cp config.py.example config.py
    $EDITOR config.py

Create a test database:

    make seed

Create an empty database:

    make init

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
