import re
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


class TestViews(fixtures.BaseCase):

    def setup(self):
        self.client = Client(Application(), BaseResponse)
        fixtures.BaseCase.setUp(self)

    def test_revision_list(self):
        response = self.client.get('/')
        assert response.status_code == 200
        assert response.template_name == 'revision_list.html'

        c = response.template_context
        assert map(attrgetter('svn_id'), c['revisions']) == [2, 1]

        d = PyQuery(response.data)
        assert re.findall('(\d+) tests', d('.total').text()) == ['22', '44']
