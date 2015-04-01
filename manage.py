#!/usr/bin/env python2
from __future__ import print_function
import sys
from dudel import manager, db, app
from dudel.models import Poll


@manager.command
def cron(verbose=False):
    """
    This view should execute some regular tasks to be called by a cronjob, e.g.
    by simply calling "./manage.py cron"
    """

    def stdout(*args, **kwargs):
        if not verbose: return
        if 'end' not in kwargs: kwargs['end'] = '\n'
        print(*args, **kwargs)

    def stderr(*args, **kwargs):
        if 'end' not in kwargs: kwargs['end'] = '\n'
        kwargs['file'] = sys.stderr
        print(*args, **kwargs)


    if "ldap" in app.config['LOGIN_PROVIDERS']:
        # Update LDAP only if it is enabled
        from dudel.plugins.ldapauth import ldap_connector

        try:
            stdout("Updating LDAP users... ", end="")
            ldap_connector.update_users()
            stdout("[DONE]")
        except Exception, e:
            stdout("[FAILED]")
            stderr("Error updating LDAP users: %s" % str(e))

        try:
            stdout("Updating LDAP groups... ", end="")
            ldap_connector.update_groups()
            stdout("[DONE]")
        except Exception, e:
            stdout("[FAILED]")
            stderr("Error updating LDAP groups: %s" % str(e))

    for poll in Poll.query.filter_by(deleted=False).all():
        if poll.should_auto_delete:
            poll.deleted = True
            stdout("Auto-deleted poll: %s" % poll.title)

    db.session.commit()

if __name__ == '__main__':
    manager.run()
