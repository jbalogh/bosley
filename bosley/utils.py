import functools
import re

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import werkzeug
from werkzeug import Local, LocalManager, Response
from werkzeug.routing import Map, Rule

import settings
import log


log.stab_java()


def engine():
    return create_engine(settings.DATABASE, convert_unicode=True)

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
    return simplejson.dumps(**context)

responders = {
    'text/html': html_responder,
    'text/javascript': json_responder
}

# Sucky things about this:
# 1. Special casing for template.
# 2. multiple mimetypes for responder (e.g. application/json)
#    are possible, but not pretty
# 3. No extra args to Response, like status
def _render(request, context, template=None):
    for mimetype in request.accept_mimetypes.itervalues():
        if mimetype in responders:
            responder = responders[mimetype]
            if template:
                content = responder(request, context, template)
            else:
                content = responder(request, context)
            return Response(content, mimetype=mimetype)
    else:
        # Should have more details, need to understand the spec.
        raise werkzeug.exceptions.NotAcceptable()


def render(template=None):
    def decorator(f):
        @functools.wraps(f)
        def inner(request, *args, **kwargs):
            context = f(request, *args, **kwargs)
            return _render(request, context, template)
        return inner
    return decorator


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


@add_to(jinja_env.filters)
def perlsub(string, regex, replacement):
    """Does a regex sub; the replacement string can have $n groups."""
    def sub(match):
        groups = match.groups()
        ret = []
        for s in re.split('(\$\d+)', replacement):
            match = re.match('\$(\d+)', s)
            if match:
                index = int(match.groups()[0]) - 1
                ret.append(groups[index])
            else:
                ret.append(s)
        return ''.join(ret)
    return re.sub(regex, sub, string)
