from pyquery import PyQuery
from lxml.etree import XMLSyntaxError

from nose.tools import assert_raises
from mock import patch

from bosley import remote, settings

import fixtures


@patch('bosley.remote.PyQuery')
def test_query(pq_mock):
    url = 'foo'
    remote.query('foo')
    kwargs = pq_mock.call_args[1]
    assert kwargs['parser'] == 'xml'
    assert kwargs['url'] == settings.BASE + url


@patch('bosley.remote.query')
def test_discover(query_mock):
    remote.discover()
    query_mock.assert_called_with('discover=1')


@patch('bosley.remote.query')
def test_test(query_mock):
    case = 'foo'
    remote.test(case)
    query_mock.assert_called_with('case=%s' % case)


def syntax_error():
    # Requires positional args, don't care what they are.
    raise XMLSyntaxError(1, 2, 3, 4)


@patch('bosley.remote.discover')
def test_cases_error(discover_mock):
    discover_mock.side_effect = syntax_error
    assert_raises(remote.DiscoveryError, remote.cases)


@patch('bosley.remote.test')
def test_analyze_error(test_mock):
    test_mock.side_effect = syntax_error
    assert_raises(remote.BrokenTest, remote.analyze, 'case')


@patch('bosley.remote.discover')
def test_cases(discover_mock):
    discover_mock.return_value = PyQuery(fixtures.discover_xml)
    assert remote.cases() == ['app_controller.test.php',
                              'controllers/addons_controller.test.php']


@patch('bosley.remote.test')
def test_analyze(test_mock):
    test_mock.return_value = PyQuery(fixtures.testcase_xml)
    assert remote.analyze('bla') == (5, 1)


@patch('bosley.remote.test')
def test_analyze2(test_mock):
    test_mock.return_value = PyQuery(fixtures.testcase_xml)
    expected = {'testDefaults': (['Default shadow db'], []),
                'testPopulated': (['Populated shadow db'], []),
                'testFallback': (['Fallback to shadow', 'Disabled shadow'],
                                 ['Shadow databases']),
                'testNoErrors': (['Should be no errors'], []),
                }
    actual = remote.analyze2('bla')
    assert actual.keys() == expected.keys()
    for name, (e_passing, e_failing) in expected.items():
        a_passing, a_failing = actual[name]
        for a, e in zip(a_passing, e_passing):
            assert a.startswith(e)
        for a, e in zip(a_failing, e_failing):
            assert a.startswith(e)


@patch('bosley.remote.test')
def test_analyze2_error(test_mock):
    test_mock.side_effect = syntax_error
    assert_raises(remote.BrokenTest, remote.analyze2, 'case')
