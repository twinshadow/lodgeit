#!/usr/bin/env python2
from os.path import dirname, join as pathjoin, exists
from sys import argv
import json

from werkzeug import script, create_environ, run_wsgi_app

from lodgeit import local
from lodgeit.application import make_app
from lodgeit.database import db

DEFAULT_CONFIG = "config_default.json"
SITE_CONFIG = "config.json"

def load_config(filename):
    with open(filename) as fd:
        return json.load(fd)

def apply_config(config, filename):
    cfg = load_config(filename)
    for cfg_section in cfg:
        if isinstance(config[cfg_section], dict):
            config[cfg_section].update(cfg[cfg_section])
        else:
            config[cfg_section] = cfg[cfg_section]

def write_config(filename, data):
    from random import choice
    if data.get("secret_key"):
        data["secret_key"] = "".join([choice(
            "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)")
            for i in range(50)])
    with open(filename, "w") as fd:
        json.dump(data, fd, indent=4, separators=(',', ': '), sort_keys=True)

def config_generate():
    workpath = dirname(argv[0])
    cfg_def = pathjoin(workpath, DEFAULT_CONFIG)
    cfg_site = pathjoin(workpath, SITE_CONFIG)
    config = load_config(cfg_def)
    if not exists(cfg_site):
        write_config(cfg_site, config)
        print("Site configuration written to %s" % cfg_site)
        exit("Please customize the site configuration before restarting the service.")
    apply_config(config, cfg_site)
    return config

def run_app(app, path='/'):
    config = config_generate()
    env = create_environ(path, config["secret_key"])
    return run_wsgi_app(app, env)

def action_runfcgi():
    from flup.server.fcgi import WSGIServer
    workpath = dirname(argv[0])
    config = config_generate()
    application = make_app(config)
    bindaddr = pathjoin(workpath, "werkzeug.sock")
    print "Binding to %s" % (bindaddr,)
    WSGIServer(application, bindAddress=bindaddr).run()

action_runserver = script.make_runserver(
    lambda: make_app(config_generate(), debug=True),
    use_reloader=True)

action_shell = script.make_shell(
    lambda: {
        'app': make_app(config_generate(), False, True),
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
