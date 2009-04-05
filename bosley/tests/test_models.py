# -*- coding: utf-8 -*-
from bosley.models import Revision, Assertion
from bosley.tests import fixtures


class TestRevisionModel(fixtures.BaseCase):

    def test_assertion_stats(self):
        rev = Revision.q.filter_by(svn_id=2).one()
        stats = rev.assertion_stats()
        assert stats['broken'] == 1
        assert stats['failing'] == 2
        assert stats['passes'] == 2
        assert stats['fails'] == 3
        assert stats['total'] == 5

    def test_unicode(self):
        session = Revision.q.session
        r = Revision(message=u'αβγδεζηθικλμνξ',
                     author=u'爆発物持者立入禁止')
        session.add(r)
        session.commit()


class TestAssertionModel(fixtures.BaseCase):

    def test_unicode(self):
        session = Assertion.q.session
        a = Assertion(text=u'αβγδεζηθικλμνξ')
        session.add(a)
        session.commit()
