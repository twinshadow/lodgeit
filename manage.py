#!/usr/bin/env python2

from werkzeug import script, create_environ, run_wsgi_app

from lodgeit import local
from lodgeit.application import make_app
from lodgeit.database import db

CONFIG = {
        "dburi": "sqlite:////tmp/lodgeit.db",
        "secret_key": "no secret key",
        "disable_captcha": False,
}

def run_app(app, path='/'):
    env = create_environ(path, SECRET_KEY)
    return run_wsgi_app(app, env)

action_runserver = script.make_runserver(
    lambda: make_app(CONFIG, debug=True),
    use_reloader=True)

action_shell = script.make_shell(
    lambda: {
        'app': make_app(CONFIG, False, True),
        'local': local,
        'db': db,
        'run_app': run_app
    },
    ('\nWelcome to the interactive shell environment of LodgeIt!\n'
     '\n'
     'You can use the following predefined objects: app, local, db.\n'
     'To run the application (creates a request) use *run_app*.')
)

if __name__ == '__main__':
    script.run()
