import re
import sys
import functools
from operator import attrgetter

import werkzeug
from pyquery import PyQuery
from werkzeug import Client, BaseResponse, Request, EnvironBuilder
from nose.tools import eq_, assert_raises
from mock import patch, sentinel, Mock

from bosley import settings, utils, views
from bosley.application import Application

import fixtures
from multipart import post_multipart


# Hijack _render to store the template name and context.
def hijack_render(old_render):
    def new_render(request, context):
        response = old_render(request, context)
        # Won't work if there's more than one BaseResponse in use.
        BaseResponse.template = context.template
        BaseResponse.context = context.context
        return response
    utils._render = new_render
hijack_render(utils._render)


def get(url, status_code=200, template='', accept='text/html'):
    def inner(f):
        @functools.wraps(f)
        def wrapper(self):
            client = Client(Application(), BaseResponse)
            response = client.get(url, headers={'Accept': accept})
            eq_(response.status_code, status_code)
            if template:
                assert response.template ==template
            f(self, response, response.context, PyQuery(response.data))
            # Validate after other tests so we know everything else works.
            # Hacky piggybacking on --verbose so tests go faster.
            if '--verbose' in sys.argv:
                validator = post_multipart('validator.w3.org', '/check',
                                           {'fragment': response.data})
                assert PyQuery(validator)('#congrats').size() == 1
        return wrapper
    return inner


def equiv(a, b):
    """Compare two strings, ignoring whitespace."""
    return ''.join(a.split()) == ''.join(b.split())


class TestViews(fixtures.BaseCase):

    def setup(self):
        self.client = Client(Application(), BaseResponse)
        fixtures.BaseCase.setUp(self)

    @get('/list/', template='revision_list.html')
    def test_revision_list(self, response, context, dom):
        assert map(attrgetter('svn_id'), context['page'].objects) == [2, 1]
        assert re.findall('(\d+) tests', dom('.total').text()) == ['5', '4']
        assert [e.attrib['href'] for e in dom('dt a')] == ['/r/2', '/r/1']
        assert all(map(equiv, [e.text for e in dom('.files')], [
            '2 failing test files, 1 broken.',
            '1 failing test files, 1 broken.',
        ]))

    @get('/r/2', template='revision_detail.html')
    def test_revision_detail(self, response, context, d):
        assert context['revision'].svn_id == 2
        assert d('#stats').text() == '5 tests: +2 -3'
        assert d('#broken').text() == 'broken.tests'
        assert d('.test').text() == 'testConfig testFallback'
        assert (d('.assertions').text() == 'Config bla bla... '
                'Shadow databases are... Fallback to shadow...')
        text = """
        config.test (1) testConfig Config bla bla... database.tests (2)
        testFallback Shadow databases are... Fallback to shadow...
        """
        assert equiv(d('#testfiles').text(), text)
        assert d('.new .test').text() == 'testConfig'
        assert d('.broke .test').text() == 'testFallback'

        # Make sure the headings are there.
        assert d('#failing-tests, #broken-tests').size() == 2

        eq_(d('.testfile').attr('href'), settings.TEST_URL % 'config.test')

    lock_mock = Mock()
    lock_mock.FileLock.return_value.is_locked.return_value = True

    @patch('bosley.views.lockfile', lock_mock)
    @get('/status', accept='text/javascript')
    def test_status(self, response, context, d):
        eq_(context['latest'], '/r/2')


@patch('bosley.views.lockfile')
@patch('bosley.views.Revision')
@patch('bosley.views.utils')
def test_status(utils_mock, revision_mock, lock_mock):
    q_mock = revision_mock.q.order_by.return_value.first.return_value
    q_mock.svn_id = sentinel.svn_id
    is_locked = lock_mock.FileLock.return_value.is_locked

    def request(accept):
        env = EnvironBuilder(headers={'Accept': accept}).get_environ()
        return Request(env)

    is_locked.return_value = False
    response = views.status(request('text/javascript'))
    eq_(response.status_code, 200)
    eq_(response.context, {'busy': False})

    is_locked.return_value = True
    utils_mock.url_for.return_value = 32
    response = views.status(request('application/json'))
    eq_(response.status_code, 200)
    eq_(response.context, {'busy': True,
                           'latest': 32})
    utils_mock.url_for.assert_called_with('revision_detail',
                                          rev=sentinel.svn_id)

    assert_raises(werkzeug.exceptions.NotAcceptable,
                  views.status, request('text/html'))


def test_no_broken():
    """Shouldn't render "Broken Tests" section."""
    context = {'broken': []}
    for name in ('revision', 'diff', 'failing', 'failures'):
        context[name] = Mock()
    d = PyQuery(utils.html_responder(Mock(), context, 'revision_detail.html'))
    assert d('#broken-tests').size() == 0
    assert d('#broken').size() == 0
