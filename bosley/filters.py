import re

from utils import add_to, jinja_env


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
