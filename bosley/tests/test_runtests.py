import sys

from mock import patch
from nose.tools import assert_raises

from bosley import runtests


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
