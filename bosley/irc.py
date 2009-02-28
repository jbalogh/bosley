import threading

import irclib

import register

# I don't want to see these in the logs.
ignore = """
all_raw_messages created endofmotd endofnames featurelist join luserchannels
luserclient luserme luserop luserunknown motd motdstart myinfo n_global n_local
ping privnotice umode yourhost
"""


def log(e):
    ignored = ignore.split()
    if e.eventtype() not in ignored:
        print e.source(), '-->', e.target()
        print e.eventtype()
        print e.arguments()


class Bot(irclib.SimpleIRCClient, register.Commander):

    def connect(self, server, nick, channel, port=6667):
        self.nick = nick
        self.port = port
        self.server = server
        self.channel = channel
        super(Bot, self).connect(server, port, nick)

    def start(self):
        # Import our not-so-decoupled plugins at the right time.
        import plugins
        try:
            threading.Thread(target=self.watcher, name='watcher').start()
            threading.Thread(target=self.cronjobs, name='cron').start()
            super(Bot, self).start()
        finally:
            self._die = True
            self.connection.close()

    def _dispatcher(self, c, e):
        log(e)
        super(Bot, self)._dispatcher(c, e)

    def on_welcome(self, c, e):
        c.join(self.channel)
        self.say('greetings humans')

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + '_')

    def say(self, s):
        self.connection.privmsg(self.channel, s)

    def run_command(self, cmd):
        try:
            if cmd in self.commands:
                self.commands[cmd](self)
        except Exception, e:
            print 'FAIL: ', cmd
            print e

    def on_pubmsg(self, c, e):
        text = e.arguments()[0]
        msg = text.split(':', 1)
        if len(msg) == 2:
            target, command = (s.strip() for s in msg)
            if target.lower() == c.get_nickname().lower():
                self.run_command(command)
        else:
            if text.startswith('!'):
                self.run_command(text[1:].strip())


if __name__ == '__main__':
    bot = Bot()
    bot.connect('irc.mozilla.org', 'bosley', '#bosley')
    bot.start()
