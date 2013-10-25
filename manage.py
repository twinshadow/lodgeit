#!/usr/bin/env python2
from os.path import dirname, join as pathjoin
from sys import argv

from werkzeug import script, create_environ, run_wsgi_app

from lodgeit import local
from lodgeit.application import make_app
from lodgeit.database import db

CONFIG = {
        "db": {
            "autoflush": True,
            "uri": "sqlite:////tmp/lodgeit.db",
        },
# python -c 'import random; print "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])'
        "secret_key": "no secret key",
        "disable_captcha": False,
        "site_title": "Lodge It"
}

def run_app(app, path='/'):
    env = create_environ(path, CONFIG["secret_key"])
    return run_wsgi_app(app, env)

def action_runfcgi():
    from flup.server.fcgi import WSGIServer
    application = make_app(CONFIG)
    bindaddr = pathjoin(str(dirname(argv[0])), "werkzeug.sock")
    print "Binding to %s" % (bindaddr,)
    WSGIServer(application, bindAddress=bindaddr).run()

action_runserver = script.make_runserver(
    lambda: make_app(CONFIG, debug=True),
    use_reloader=True)

action_shell = script.make_shell(
    lambda: {
        'app': make_app(CONFIG, False, True),
        'local': local,
        'db': db,
        'run_app': run_app,
    },
    ('\nWelcome to the interactive shell environment of LodgeIt!\n'
     '\n'
     'You can use the following predefined objects: app, local, db.\n'
     'To run the application (creates a request) use *run_app*.')
)

if __name__ == '__main__':
    script.run()
