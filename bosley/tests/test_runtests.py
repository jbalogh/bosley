import itertools
import sys
from operator import itemgetter

from mock import patch, Mock, sentinel
from nose.tools import assert_raises

from bosley import runtests

import fixtures


class TestCase(fixtures.BaseCase):

    @patch('bosley.runtests.vcs')
    @patch('bosley.runtests.handle')
    def test_update(self, vcs_mock, handle_mock):
        commit_mock = Mock()
        commit_mock.id = 3
        vcs_mock.following.return_value = itertools.repeat(commit_mock, 2)

        runtests.update()

        methods = map(itemgetter(0), vcs_mock.method_calls)
        assert methods == ['checkout', 'rebase', 'following']

        vcs_mock.following.assert_called_with('2' * 40)

        handle_mock.assert_called_with(3)
        assert handle_mock.call_count == 2

    @patch('bosley.runtests.vcs')
    @patch('bosley.runtests.process_commits')
    def test_backfill(self, vcs_mock, process_mock):
        vcs_mock.before.return_value = sentinel.Before
        runtests.backfill()

        vcs_mock.before.assert_called_with('1' * 40)

        generator = process_mock.call_args[0][0]
        assert generator.next() == sentinel.Before
        vcs_mock.before.return_value = sentinel.Before2
        assert generator.next() == sentinel.Before2

    @patch('bosley.runtests.vcs')
    @patch('bosley.runtests.process_commits')
    @patch('bosley.runtests.Revision')
    def test_backfill_first_call(self, vcs_mock, process_mock, revision_mock):
        mock_query = Mock()
        mock_query.first.return_value = None
        revision_mock.query.order_by.return_value = mock_query

        vcs_mock.repo.commits.return_value = [sentinel.Commit]
        runtests.backfill()

        generator = process_mock.call_args[0][0]
        assert generator.next() == sentinel.Commit


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
