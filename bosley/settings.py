import os

ROOT = os.path.abspath(os.path.dirname(__file__))
path = lambda x: os.path.join(ROOT, x)

DATABASE = 'sqlite:///' + path('db.sqlite')

REPO = os.path.expanduser('~/public_html/bot/amo')

BASE = 'http://bot.khan.mozilla.org/amo/site/en-US/firefox/tests/xml/?'

TEMPLATE_PATH = path('templates')

REVISION_DETAIL_URL = 'http://jbalogh.khan.mozilla.org:5000/r/%s'

TEST_URL = 'http://bot.khan.mozilla.org/amo/site/en-US/firefox/tests?case=%s'

BUGZILLA_BUG = 'https://bugzilla.mozilla.org/show_bug.cgi?id=%s'

try:
    from local_settings import *
except ImportError:
    pass
