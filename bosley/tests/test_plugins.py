from mock import patch, Mock

from bosley import plugins, settings

import fixtures


def test_gtfo():
    bot_mock = Mock()
    plugins.gtfo(bot_mock)
    bot_mock.say.assert_called_with('stfu')


@patch('bosley.plugins.threading')
def test_wtf(threading_mock):
    bot_mock, thread_mock = Mock(), Mock()
    thread_mock.getName.return_value = 'name'
    threading_mock.enumerate.return_value = [thread_mock, thread_mock]
    plugins.wtf(bot_mock)
    bot_mock.say.assert_called_with('name, name')


def test_help():
    bot_mock = Mock()
    bot_mock.commands = ['foo', 'bar']
    plugins.help(bot_mock)
    bot_mock.say.assert_called_with('bar, foo')


class TestPlugins(fixtures.BaseCase):

    def test_status(self):
        bot_mock = Mock()
        plugins.status(bot_mock)
        bot_mock.say.assert_called_with(
            'r2 (fred): -1 passing, +3 failing (%s)'
            % settings.REVISION_DETAIL_URL % 2)

    @patch('bosley.plugins.runtests')
    def test_updater(self, runtests_mock):
        bot_mock = Mock()
        plugins.updater(bot_mock)
        assert runtests_mock.update.called
        assert bot_mock.run_command.called is False

    @patch('bosley.plugins.st')
    @patch('bosley.plugins.Revision')
    @patch('bosley.plugins.runtests')
    def test_updater_changes(self, runtests_mock, revision_mock, st_mock):
        bot_mock, q_mock = Mock(), Mock()
        revision_mock.q.order_by.return_value = q_mock
        q_mock.first = [Mock(), Mock(), Mock(), Mock()].pop

        st_mock.return_value = 1, 2, 3
        plugins.updater(bot_mock)
        assert runtests_mock.update.called
        assert bot_mock.run_command.called

        runtests_mock.reset_mock(), bot_mock.reset_mock()

        st_mock.return_value = 1, 0, 0
        plugins.updater(bot_mock)
        assert runtests_mock.update.called
        assert bot_mock.run_command.called is False

    def test_report(self):
        bot_mock = Mock()
        plugins.report(bot_mock)
        calls = [args[0][0] for args in bot_mock.say.call_args_list]
        assert calls == ['6 tests: +2 -4', '2 failing test files, 1 broken']
