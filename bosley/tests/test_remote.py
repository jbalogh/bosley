from pyquery import PyQuery
from lxml.etree import XMLSyntaxError

from nose.tools import assert_raises
from mock import patch

from bosley import remote, settings


# Some test data.
testcase_xml = """
<?xml version="1.0"?>
<run>
  <group size="2">
    <name>Test Case: database.test.php</name>
    <group size="1">
      <name>/bot/amo/site/app/tests/database.test.php</name>
      <case>
        <name>DatabaseTest</name>
        <test>
          <name>testDefaults</name>
          <pass>Default shadow db config does not cause SHADOW constants to be set at [/bot/amo/site/app/tests/database.test.php line 79]</pass>
        </test>
        <test>
          <name>testPopulated</name>
          <pass>Populated shadow db config returns 1 database at [/bot/amo/site/app/tests/database.test.php line 85]</pass>
        </test>
        <test>
          <name>testFallback</name>
          <pass>Fallback to shadow database 2 when shadow database 1 is down at [/bot/amo/site/app/tests/database.test.php line 109]</pass>
          <fail>Shadow databases are still enabled at [/bot/amo/site/app/tests/database.test.php line 110]</fail>
          <pass>Disabled shadow databases because all shadows are down at [/bot/amo/site/app/tests/database.test.php line 124]</pass>
        </test>
      </case>
    </group>
    <group size="1">
      <name>/bot/amo/site/app/tests/global.test.php</name>
      <case>
        <name>GlobalTest</name>
        <test>
          <name>testNoErrors</name>
          <pass>Should be no errors at [/bot/amo/site/app/tests/global.test.php line 46]</pass>
        </test>
      </case>
    </group>
  </group>
</run>
"""

discover_xml = """
<?xml version="1.0" ?>
<cases>
  <case>app_controller.test.php</case>
  <case>controllers/addons_controller.test.php</case>
</cases>
"""


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
    discover_mock.return_value = PyQuery(discover_xml)
    assert remote.cases() == ['app_controller.test.php',
                              'controllers/addons_controller.test.php']


@patch('bosley.remote.test')
def test_analyze(test_mock):
    test_mock.return_value = PyQuery(testcase_xml)
    assert remote.analyze('bla') == (5, 1)


@patch('bosley.remote.test')
def test_analyze2(test_mock):
    test_mock.return_value = PyQuery(testcase_xml)
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
