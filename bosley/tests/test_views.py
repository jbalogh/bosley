import re
import functools
from operator import attrgetter

from pyquery import PyQuery
from werkzeug import Client, BaseResponse

from bosley import utils, views
from bosley.application import Application
from bosley.tests import fixtures


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
        return wrapper
    return inner


class TestViews(fixtures.BaseCase):

    def setup(self):
        self.client = Client(Application(), BaseResponse)
        fixtures.BaseCase.setUp(self)

    @get('/', template_name='revision_list.html')
    def test_revision_list(self, response, context, dom):
        assert map(attrgetter('svn_id'), context['revisions']) == [2, 1]
        assert re.findall('(\d+) tests', dom('.total').text()) == ['22', '44']

    @get('/1', template_name='revision_detail.html')
    def test_revision_detail(self, response, context, d):
        assert context['revision'].svn_id == 1
        assert d('#stats').text() == '44 tests: +42 -2'
        assert d('#failing').text() == 'failing case ( 2 )'
        assert d('#broken').text() == 'broken case'


