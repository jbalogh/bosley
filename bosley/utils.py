import re
import logging

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug import Local, LocalManager, Response
from werkzeug.routing import Map, Rule

import settings


logging.basicConfig(filename=settings.path('log'), level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s:%(name)s:%(message)s')


def engine():
    return create_engine(settings.DATABASE, convert_unicode=True)

metadata = MetaData()
Session = scoped_session(sessionmaker(bind=engine()))

# Werkzeug stuff.
local = Local()
local_manager = LocalManager([local])
application = local('application')
url_map = Map([
    Rule('/media/<file>', endpoint='media', build_only=True),
])


def expose(rule, **kw):

    def decorate(f):
        kw['endpoint'] = f.__name__
        url_map.add(Rule(rule, **kw))
        return f
    return decorate


def url_for(endpoint, _external=False, **values):
    return local.url_adapter.build(endpoint, values, force_external=_external)


jinja_env = Environment(loader=FileSystemLoader(settings.TEMPLATE_PATH))
jinja_env.globals['url_for'] = url_for


def render_template(template, **context):
    return Response(jinja_env.get_template(template).render(**context),
                    mimetype='text/html')


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

jinja_env.filters['perlsub'] = perlsub
