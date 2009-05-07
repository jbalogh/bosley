import werkzeug
from werkzeug import script


def make_app():
    from bosley.application import Application
    return werkzeug.DebuggedApplication(Application(), evalex=True)


def make_shell():
    from bosley import models, utils
    application = make_app()
    return {'application': application, 'models': models, 'utils': utils}


action_runserver = script.make_runserver(make_app, use_reloader=True)
action_shell = script.make_shell(make_shell)

if __name__ == '__main__':
    script.run()
