import werkzeug
from werkzeug import Request, EnvironBuilder

from mock import Mock, patch
from nose.tools import assert_raises

from bosley import utils


@patch('bosley.utils.Response', Mock())
@patch('bosley.utils.json_responder')
@patch('bosley.utils.html_responder')
def test_render(html_mock, json_mock):

    def request(accept):
        env = EnvironBuilder(headers={'Accept': accept}).get_environ()
        return Request(env)

    Mock.__iter__ = lambda self: iter([])
    context_mock = Mock()
    context_mock.kwargs = {}
    utils._render(request('text/html'), context_mock)
    assert html_mock.called


    utils._render(request('text/javascript'), context_mock)
    assert json_mock.called

    assert_raises(werkzeug.exceptions.NotAcceptable,
                  utils._render, request('wtf'), {})
