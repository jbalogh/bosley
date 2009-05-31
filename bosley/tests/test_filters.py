from nose.tools import eq_

from bosley import filters, settings


def test_perlsub():
    assert filters.perlsub('foobar', '(foo)(bar)', '$2x$1') == 'barxfoo'


def test_bugzilla():
    bug = '499234'
    url = settings.BUGZILLA_BUG % bug
    eq_(filters.bugzilla('I <3 bug %s!' % bug), 'I <3 %s!' % url)
