# -*- coding: utf-8 -*-
from __future__ import with_statement

from datetime import datetime

from mock import patch
from nose.tools import eq_

from bosley.models import Revision, Assertion
from bosley.tests import fixtures


class TestRevisionModel(fixtures.BaseCase):

    def test_assertion_stats(self):
        rev = Revision.q.filter_by(svn_id=2).one()
        stats = rev.assertion_stats()
        assert stats['broken'] == 1
        assert stats['failing'] == 2
        assert stats['passes'] == 2
        assert stats['fails'] == 4
        assert stats['total'] == 6

    def test_unicode(self):
        session = Revision.q.session
        r = Revision(message=u'αβγδεζηθικλμνξ',
                     author=u'爆発物持者立入禁止')
        session.add(r)
        session.commit()

    @patch('bosley.cache.cache')
    def test_cache(self, cache_mock):
        cache_mock.get.return_value = None

        rev = Revision.q.filter_by(svn_id=2).one()
        stats = rev.assertion_stats()

        # The key is the function name plus the args.
        key = 'assertion_stats:' + rev.cache_key
        cache_mock.get.assert_called_with(key)
        # The first positional argument is the key.
        assert cache_mock.set.call_args[0][0] == key

    def test_cache_invalidation(self):
        rev = Revision.q.filter_by(svn_id=2).one()
        old_key = rev.cache_key
        old_stats = rev.assertion_stats()

        rev.test_date = datetime.now()
        new_key = 'assertion_stats:' + rev.cache_key

        assert old_key != new_key

        with patch('bosley.cache.cache.set') as cache_set_mock:
            new_stats = rev.assertion_stats()
            eq_(cache_set_mock.call_args[0][0], new_key)


class TestAssertionModel(fixtures.BaseCase):

    def test_unicode(self):
        session = Assertion.q.session
        a = Assertion(text=u'αβγδεζηθικλμνξ')
        session.add(a)
        session.commit()
