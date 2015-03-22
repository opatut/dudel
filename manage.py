#!/usr/bin/env python2
from __future__ import print_function
import sys
from dudel import manager, db, app
from dudel.models import Poll


@manager.command
def cron():
    """
    This view should execute some regular tasks to be called by a cronjob, e.g.
    by simply calling "./manage.py cron"
    """

    if "ldap" in app.config['LOGIN_PROVIDERS']:
        # Update LDAP only if it is enabled
        from dudel.plugins.ldapauth import ldap_connector

        try:
            ldap_connector.update_users()
            print("updated LDAP users\n")
        except Exception, e:
            print("error updating LDAP users: %s\n" % str(e), file=sys.stderr)

        try:
            ldap_connector.update_groups()
            print("updated LDAP groups\n")
        except Exception, e:
            print("error updating LDAP groups: %s\n" % str(e), file=sys.stderr)

    for poll in Poll.query.filter_by(deleted=False).all():
        if poll.should_auto_delete:
            poll.deleted = True
            print("auto-deleted poll: %s\n" % poll.title)

    db.session.commit()

if __name__ == '__main__':
    manager.run()
