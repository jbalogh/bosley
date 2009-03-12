import re
import sys
import functools
from operator import attrgetter

from pyquery import PyQuery
from werkzeug import Client, BaseResponse

from bosley import utils, views
from bosley.application import Application

import fixtures
from multipart import post_multipart


# Hijack render_template to store the name and context.
def render(template, **context):
    # Not threadsafe.
    BaseResponse.template_name = template
    BaseResponse.template_context = context
    return utils.render_template(template, **context)
views.render_template = render


def get(url, status_code=200, template_name=''):
    def inner(f):
        @functools.wraps(f)
        def wrapper(self):
            response = Client(Application(), BaseResponse).get(url)
            assert response.status_code == status_code
            if template_name:
                assert response.template_name == template_name
            f(self, response, response.template_context,
              PyQuery(response.data))
            # Validate after other tests so we know everything else works.
            # Hacky piggybacking on --verbose so tests go faster.
            if '--verbose' in sys.argv:
                validator = post_multipart('validator.w3.org', '/check',
                                           {'fragment': response.data})
                assert PyQuery(validator)('#congrats').size() == 1
        return wrapper
    return inner


class TestViews(fixtures.BaseCase):

    def setup(self):
        self.client = Client(Application(), BaseResponse)
        fixtures.BaseCase.setUp(self)

    @get('/', template_name='revision_list.html')
    def test_revision_list(self, response, context, dom):
        assert map(attrgetter('svn_id'), context['revisions']) == [2, 1]
        assert re.findall('(\d+) tests', dom('.total').text()) == ['5', '4']
        assert [e.attrib['href'] for e in dom('dt a')] == ['/2', '/1']

    @get('/2', template_name='revision_detail.html')
    def test_revision_detail(self, response, context, d):
        assert context['revision'].svn_id == 2
        assert d('#stats').text() == '5 tests: +2 -3'
        assert d('#failing').text() == 'database.tests ( 2 ) config.test ( 1 )'
        assert d('#broken').text() == 'broken.tests'
