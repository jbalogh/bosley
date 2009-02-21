from werkzeug import script

def make_app():
    from bosley.application import Application
    return Application()


def make_shell():
    from bosley import models, utils
    application = make_app()
    return locals()


action_runserver = script.make_runserver(make_app, use_reloader=True)
action_shell = script.make_shell(make_shell)
action_initdb = lambda: make_app().init_database()

if __name__ == '__main__':
    script.run()
