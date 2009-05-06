import werkzeug
from werkzeug import Request, EnvironBuilder

from mock import Mock, patch
from nose.tools import assert_raises

from bosley import utils

def test_perlsub():
    assert utils.perlsub('foobar', '(foo)(bar)', '$2$1') == 'barfoo'


@patch('bosley.utils.Response', Mock())
def test_render():
    old_responders = utils.responders
    html_mock, json_mock = Mock(), Mock()
    utils.responders = {'text/html': html_mock,
                        'text/javascript': json_mock}

    def request(accept):
        env = EnvironBuilder(headers={'Accept': accept}).get_environ()
        return Request(env)

    utils._render(request('text/html'), {}, 'template')
    assert html_mock.called


    utils._render(request('text/javascript'), {})
    assert json_mock.called

    assert_raises(werkzeug.exceptions.NotAcceptable,
                  utils._render, request('wtf'), {})

    utils.responders = old_responders
