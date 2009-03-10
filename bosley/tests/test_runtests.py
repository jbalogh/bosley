import sys
from operator import itemgetter

from mock import patch, Mock
from nose.tools import assert_raises

from bosley import runtests

import fixtures


class TestCase(fixtures.BaseCase):

    @patch('bosley.runtests.vcs')
    @patch('bosley.runtests.handle')
    def test_update(self, vcs_mock, handle_mock):
        commit_mock = Mock()
        commit_mock.id = 3
        vcs_mock.following.return_value = [commit_mock]

        runtests.update()

        methods = map(itemgetter(0), vcs_mock.method_calls)
        assert methods == ['checkout', 'rebase', 'following']

        vcs_mock.following.assert_called_with('2' * 40)

        handle_mock.assert_called_with(3)
        assert handle_mock.call_count == 1


@patch('bosley.runtests.backfill')
@patch('bosley.runtests.update')
@patch('sys.exit')
def test_main(backfill_mock, update_mock, exit_mock):
    # Save it so we can reset it later.
    _argv = sys.argv

    sys.argv = ['./runtests', 'update']
    runtests.main()
    assert update_mock.called

    sys.argv = ['./runtests', 'backfill']
    runtests.main()
    assert backfill_mock.called

    def system_exit():
        raise SystemExit
    exit_mock.side_effect = system_exit

    sys.argv = ['./runtests']
    assert_raises(SystemExit, runtests.main)

    sys.argv = ['./runtests', 'bla']
    assert_raises(SystemExit, runtests.main)

    sys.argv = ['./runtests', 'foo', 'bar']
    assert_raises(SystemExit, runtests.main)

    sys.argv = _argv
