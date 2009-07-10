import re

import settings
from utils import add_to, jinja_env


@add_to(jinja_env.filters)
def bugzilla(text):
    link = '<a href="%s">$0</a>' % (settings.BUGZILLA_BUG % '$1')
    return perlsub(text, 'bug (\d+)', link)


@add_to(jinja_env.filters)
def perlsub(string, regex, replacement):
    """Does a regex sub; the replacement string can have $n groups."""
    def sub(match):
        ret = []
        for s in re.split('(\$\d+)', replacement):
            m = re.match('\$(\d+)', s)
            if m:
                index = int(m.groups()[0])
                ret.append(match.group(index))
            else:
                ret.append(s)
        return ''.join(ret)
    return re.sub(regex, sub, string)
