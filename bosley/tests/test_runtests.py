import itertools
import sys
from operator import itemgetter

from mock import patch, Mock, sentinel
from nose.tools import assert_raises

from bosley import runtests, remote

import fixtures


def methods(mock):
    return map(itemgetter(0), mock.method_calls)


class TestCase(fixtures.BaseCase):

    @patch('bosley.runtests.vcs')
    @patch('bosley.runtests.handle')
    def test_update(self, vcs_mock, handle_mock):
        commit_mock = Mock()
        commit_mock.id = 3
        vcs_mock.following.return_value = itertools.repeat(commit_mock, 2)

        runtests.update()

        assert methods(vcs_mock) == ['checkout', 'rebase', 'following']
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


@patch('bosley.runtests.vcs')
@patch('bosley.runtests.remote.cases')
@patch('bosley.runtests.test_commit')
def test_handle(vcs_mock, remote_mock, test_commit_mock):
    commit = sentinel.Commit
    runtests.handle(commit)

    vcs_mock.checkout.assert_called_with(commit)
    vcs_mock.reset.assert_called_with(commit)
    assert methods(vcs_mock) == ['checkout', 'reset']

    assert remote.cases.called
    test_commit_mock.assert_called_with(commit)


@patch('bosley.runtests.vcs')
@patch('bosley.runtests.remote.cases')
@patch('bosley.runtests.test_commit')
def test_handle_error(vcs_mock, remote_mock, test_commit_mock):
    def discovery_error():
        raise remote.DiscoveryError
    remote_mock.side_effect = discovery_error

    commit = sentinel.Commit
    runtests.handle(commit)

    assert methods(vcs_mock) == ['checkout', 'apply_testing_patch', 'reset']
