import functools
import re

import simplejson
import werkzeug
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug import Local, LocalManager, Response
from werkzeug.routing import Map, Rule

import settings
import log


log.stab_java()


def engine():
    return create_engine(settings.DATABASE, convert_unicode=True,
                         pool_recycle=40)

metadata = MetaData()
Session = scoped_session(sessionmaker(bind=engine()))

# Werkzeug stuff.
local = Local()
local_manager = LocalManager([local])
application = local('application')
url_map = Map([
    Rule('/', redirect_to='/list/'),
    Rule('/r/', redirect_to='/list/'),
    Rule('/media/<file>', endpoint='media', build_only=True),
])

jinja_env = Environment(loader=FileSystemLoader(settings.TEMPLATE_PATH))


def add_to(dict, name=None):
    def decorator(f):
        dict[name or f.__name__] = f
        return f
    return decorator


def expose(rule, **kw):
    def decorate(f):
        kw['endpoint'] = f.__name__
        url_map.add(Rule(rule, **kw))
        return f
    return decorate


@add_to(jinja_env.globals)
def url_for(endpoint, _external=False, **values):
    return local.url_adapter.build(endpoint, values, force_external=_external)


def html_responder(request, context, template):
    return jinja_env.get_template(template).render(**context)


def json_responder(request, context):
    return simplejson.dumps(context)


def _render(request, context):
    # Hardcoding FTW!
    mimetypes = request.accept_mimetypes
    if (mimetypes.accept_html or mimetypes.accept_xhtml) and context.template:
        content = html_responder(request, context.context, context.template)
        mimetype = 'text/html'
    elif 'text/javascript' in mimetypes or 'application/json' in mimetypes:
        content = json_responder(request, context.context)
        mimetype = 'text/javascript'
    else:
        # Should have details on what is acceptable.
        raise werkzeug.exceptions.NotAcceptable()
    response = Response(content, mimetype=mimetype, **context.kwargs)
    headers = response.headers
    headers.add_header('Vary', 'Accept')
    headers.add_header('Cache-Control', 'public, must-revalidate, max-age=0')
    return response


def render(template=None):
    def decorator(f):
        @functools.wraps(f)
        def inner(request, *args, **kwargs):
            context = f(request, *args, **kwargs)
            context.template = template
            return _render(request, context)
        return inner
    return decorator


class Context(object):

    def __init__(self, context, **kwargs):
        self.context = context
        self.kwargs = kwargs


def json(f):
    return render(None)(f)


def force_unicode(s, encoding='utf-8', errors='strict'):
    # Thanks Django.
    if not isinstance(s, basestring):
        if hasattr(s, '__unicode__'):
            s = unicode(s)
        else:
            try:
                s = unicode(str(s), encoding, errors)
            except UnicodeEncodeError:
                pass
    elif not isinstance(s, unicode):
        s = s.decode(encoding, errors)
    return s
