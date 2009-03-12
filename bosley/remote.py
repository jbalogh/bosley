from pyquery import PyQuery
from lxml.etree import XMLSyntaxError
import httplib2

import settings


class BrokenTest(Exception):
    pass


class DiscoveryError(Exception):
    pass


def query(url):
    # Sometimes the tests hang, so use an explicit timeout.
    h = httplib2.Http(timeout=60)
    resp, content = h.request(settings.BASE + url)
    # Force XML parser so we're not forgiving on errors.  Exceptions induce
    # invalid output, so we want those caught and shown as an error.
    return PyQuery(content, parser='xml')


def discover():
    return query('discover=1')


def cases():
    try:
        d = discover()
    except XMLSyntaxError:
        raise DiscoveryError
    return [e.text for e in d('case')]


def test(case):
    return query('case=' + case)


def analyze(case):
    try:
        d = test(case)
    except XMLSyntaxError:
        raise BrokenTest
    return d('pass').size(), d('fail').size()


def analyze2(case):
    try:
        d = test(case)
    except XMLSyntaxError:
        raise BrokenTest
    except:
        raise BrokenTest
    tests = {}
    for name in d('test name'):
        f = lambda tag: [e.text for e in name.itersiblings() if e.tag == tag]
        tests[name.text] = f('pass'), f('fail')
    return tests
