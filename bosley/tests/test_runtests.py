import itertools
import sys
from operator import itemgetter

from pyquery import PyQuery
from mock import patch, Mock, sentinel
from nose.tools import assert_raises

from bosley import runtests, remote
from bosley.models import (Revision, TestFile, Assertion,
                           Test, Result, BrokenTest)

import fixtures


def methods(mock):
    return map(itemgetter(0), mock.method_calls)


class TestCase(fixtures.BaseCase):

    @patch('bosley.runtests.handle')
    @patch('bosley.runtests.vcs')
    def test_update(self, vcs_mock, handle_mock):
        commit_mock = Mock()
        commit_mock.id = 3
        vcs_mock.following.return_value = itertools.repeat(commit_mock, 2)

        runtests.update()

        assert methods(vcs_mock) == ['checkout', 'rebase', 'following']
        vcs_mock.following.assert_called_with('2' * 40)

        handle_mock.assert_called_with(3)
        assert handle_mock.call_count == 2

    @patch('bosley.runtests.process_commits')
    @patch('bosley.runtests.vcs')
    def test_backfill(self, vcs_mock, process_mock):
        vcs_mock.before.return_value = sentinel.Before
        runtests.backfill()

        vcs_mock.before.assert_called_with('1' * 40)

        generator = process_mock.call_args[0][0]
        assert generator.next() == sentinel.Before
        vcs_mock.before.return_value = sentinel.Before2
        assert generator.next() == sentinel.Before2

    @patch('bosley.runtests.Revision')
    @patch('bosley.runtests.process_commits')
    @patch('bosley.runtests.vcs')
    def test_backfill_first_call(self, vcs_mock, process_mock, revision_mock):
        mock_query = Mock()
        mock_query.first.return_value = None
        revision_mock.q.order_by.return_value = mock_query

        vcs_mock.repo.commits.return_value = [sentinel.Commit]
        runtests.backfill()

        generator = process_mock.call_args[0][0]
        assert generator.next() == sentinel.Commit

    @patch('bosley.runtests.test_revision')
    @patch('bosley.runtests.vcs.info')
    def test_test_commit(self, info_mock, test_revision_mock):
        git_id = '3' * 40
        info_mock.return_value = {'git_id': git_id,
                                  'message': u'I\xf1t\xebrn\xe2ti\xf4n\xe0l',
                                  'author': u'\u03bcs\xeb\u044f'}
        runtests.test_commit(sentinel.id)
        assert Revision.q.filter_by(git_id=git_id).count() == 1

    @patch('bosley.runtests.test_revision')
    @patch('bosley.runtests.vcs.info')
    def test_test_commit_existing(self, info_mock, test_revision_mock):
        info_mock.return_value = {'git_id': '2' * 40}
        runtests.test_commit(sentinel.id)
        assert test_revision_mock.called is False

    @patch('bosley.runtests.log')
    def test_run(self, log_mock):
        queue_mock = Mock()
        queue = [True, False]
        queue_mock.empty = queue.pop

        testfile_name = u'testfile'
        queue_mock.get.return_value = testfile_name

        tester = runtests.ThreadedTester2(queue_mock, 5)
        tester.test = Mock()

        tester.run()

        assert TestFile.q.filter_by(name=testfile_name).count() == 1

    @patch('bosley.remote.test')
    def test_test_runner(self, test_mock):
        test_mock.return_value = PyQuery(fixtures.testcase_xml)

        rev = 5
        tester = runtests.ThreadedTester2(Mock(), rev)
        testfile = TestFile()
        tester.test(testfile)

        names = 'testFallback testNoErrors testDefaults testPopulated'.split()
        assert [t.name for t in testfile.tests] == names

        q = Result.q.filter_by(revision_id=rev)
        assert q.count() == 6
        assert q.filter_by(fail=True).count() == 1
        q = q.join(Assertion).join(Test)
        assert q.filter(Test.name == u'testFallback').count() == 3

    @patch('bosley.runtests.remote.analyze2')
    def test_test_runner_error(self, analyze_mock):

        def broken_test(*args):
            raise remote.BrokenTest
        analyze_mock.side_effect = broken_test

        rev = 7
        tester = runtests.ThreadedTester2(Mock(), rev)
        testfile = TestFile()
        tester.test(testfile)

        assert BrokenTest.q.filter_by(revision_id=rev).count() == 1


@patch('sys.exit')
@patch('bosley.runtests.update')
@patch('bosley.runtests.backfill')
def test_main(backfill_mock, update_mock, exit_mock):
    # Save it so we can reset it later.
    _argv = sys.argv

    sys.argv = ['./runtests', 'update']
    runtests.main()
    assert update_mock.called

    sys.argv = ['./runtests', 'backfill']
    runtests.main()
    assert backfill_mock.called

    def system_exit(*args):
        raise SystemExit
    exit_mock.side_effect = system_exit

    sys.argv = ['./runtests']
    assert_raises(SystemExit, runtests.main)

    sys.argv = ['./runtests', 'bla']
    assert_raises(SystemExit, runtests.main)

    sys.argv = ['./runtests', 'foo', 'bar']
    assert_raises(SystemExit, runtests.main)

    sys.argv = _argv


@patch('bosley.runtests.test_commit')
@patch('bosley.runtests.remote.cases')
@patch('bosley.runtests.vcs')
def test_handle(vcs_mock, remote_mock, test_commit_mock):
    commit = sentinel.Commit
    runtests.handle(commit)

    vcs_mock.checkout.assert_called_with(commit)
    vcs_mock.reset.assert_called_with(commit)
    assert methods(vcs_mock) == ['checkout', 'reset']

    assert remote.cases.called
    test_commit_mock.assert_called_with(commit)


@patch('bosley.runtests.test_commit')
@patch('bosley.runtests.remote.cases')
@patch('bosley.runtests.vcs')
def test_handle_error(vcs_mock, remote_mock, test_commit_mock):

    def discovery_error(*args):
        raise remote.DiscoveryError
    remote_mock.side_effect = discovery_error

    commit = sentinel.Commit
    runtests.handle(commit)

    assert methods(vcs_mock) == ['checkout', 'apply_testing_patch', 'reset']
