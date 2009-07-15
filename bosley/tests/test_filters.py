from nose.tools import eq_

from bosley import filters, settings


def test_perlsub():
    eq_(filters.perlsub('foobar', '(foo)(bar)', '$2x$1'), 'barxfoo')
    eq_(filters.perlsub('foo', 'o', '$0'), 'foo')


def test_bugzilla():
    bug = '499234'
    link = '<a href="%s">bug %s</a>' % (settings.BUGZILLA_BUG % bug, bug)
    eq_(filters.bugzilla('I <3 bug %s!' % bug), 'I <3 %s!' % link)
