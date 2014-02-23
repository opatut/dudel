default: run

setup:
	pip install --upgrade flask flask-sqlalchemy flask-wtf flask-login flask-markdown python-dateutil python-ldap raven blinker flask-gravatar

init:
	python2 scripts/init.py

seed:
	python2 scripts/seed.py

run:
	python2 scripts/run.py
