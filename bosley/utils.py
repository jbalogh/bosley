import logging

from jinja import Environment, FileSystemLoader
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import create_session, scoped_session, sessionmaker
from werkzeug import Local, LocalManager, Response
from werkzeug.routing import Map, Rule

import settings


logging.basicConfig(filename=settings.path('log'), level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s:%(name)s:%(message)s')

local = Local()
local_manager = LocalManager([local])
application = local('application')

metadata = MetaData()


def get_session(wsgi=False):
    if wsgi:
        def create():
            return create_session(application.engine, autocommit=False)
        return scoped_session(create, local_manager.get_ident)
    else:
        return sessionmaker(bind=engine())()


def engine():
    return create_engine(settings.DATABASE, convert_unicode=True)


url_map = Map()
def expose(rule, **kw):
    def decorate(f):
        kw['endpoint'] = f.__name__
        url_map.add(Rule(rule, **kw))
        return f
    return decorate


def url_for(endpoint, external=False, **values):
    return local.url_adapter.build(endpoint, values, force_external=external)


jinja_env = Environment(loader=FileSystemLoader(settings.TEMPLATE_PATH))
jinja_env.globals['url_for'] = url_for


def render_template(template, **context):
    return Response(jinja_env.get_template(template).render(**context),
                    mimetype='text/html')
