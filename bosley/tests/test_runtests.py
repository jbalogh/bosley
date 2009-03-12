import itertools
import sys
from operator import itemgetter

from pyquery import PyQuery
from mock import patch, Mock, sentinel
from nose.tools import assert_raises

from bosley import runtests, remote
from bosley.models import Revision, TestFile, Assertion, Test

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

    @patch('bosley.runtests.vcs.info')
    @patch('bosley.runtests.test_revision')
    def test_test_commit(self, info_mock, test_revision_mock):
        git_id = '3' * 40
        info_mock.return_value = {'git_id': git_id}
        runtests.test_commit(sentinel.id)
        assert Revision.query.filter_by(git_id=git_id).count() == 1

    @patch('bosley.runtests.vcs.info')
    @patch('bosley.runtests.test_revision')
    def test_test_commit_existing(self, info_mock, test_revision_mock):
        info_mock.return_value = {'git_id': '2' * 40}
        runtests.test_commit(sentinel.id)
        assert test_revision_mock.called is False

    @patch('bosley.runtests.log')
    def test_run(self, log_mock):
        queue_mock = Mock()
        queue = [True, False]
        queue_mock.empty = queue.pop

        testfile_name = 'testfile'
        queue_mock.get.return_value = testfile_name

        tester = runtests.ThreadedTester2(queue_mock, 5)
        tester.test = Mock()

        tester.run()

        assert TestFile.query.filter_by(name=testfile_name).count() == 1

    @patch('bosley.remote.test')
    def test_test_runner(self, test_mock):
        testfile = Mock()
        testfile.tests = []
        test_mock.return_value = PyQuery(fixtures.testcase_xml)

        tester = runtests.ThreadedTester2(Mock(), 5)
        tester.test(testfile)

        names = 'testFallback testNoErrors testDefaults testPopulated'.split()
        assert [t.name for t in testfile.tests] == names

        q = Assertion.query
        assert q.count() == 6
        assert q.filter_by(fail=True).count() == 1
        assert q.join(Test).filter(Test.name == 'testFallback').count() == 3

    @patch('bosley.runtests.remote.analyze2')
    def test_test_runner_error(self, analyze_mock):

        def broken_test():
            raise remote.BrokenTest
        analyze_mock.side_effect = broken_test

        testfile = Mock()
        tester = runtests.ThreadedTester2(Mock(), Mock())
        tester.test(testfile)

        assert testfile.broken is True


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
