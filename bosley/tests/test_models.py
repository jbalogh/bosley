# -*- coding: utf-8 -*-
from bosley.models import Result, Revision, Assertion
from bosley.tests import fixtures


class TestResultModel(fixtures.BaseCase):

    def test_query(self):
        assert Result.query.filter_by(broken=True).count() == 1


class TestRevisionModel(fixtures.BaseCase):

    def test_results(self):
        rev = Revision.query.filter_by(svn_id=1).one()
        assert rev.results.count() == 4

    def test_assertion_stats(self):
        rev = Revision.query.filter_by(svn_id=1).one()
        stats = rev.assertion_stats()
        assert stats['broken'] == 1
        assert stats['failing'] == 1
        assert stats['passes'] == 3
        assert stats['fails'] == 1
        assert stats['total'] == 4

    def test_stats(self):
        rev = Revision.query.filter_by(svn_id=1).one()
        stats = rev.stats()
        assert stats['broken'] == 1
        assert stats['failing'] == 1
        assert stats['passes'] == 42
        assert stats['fails'] == 2
        assert stats['total'] == 44

    def test_assertions(self):
        rev = Revision.query.filter_by(svn_id=1).one()
        assert rev.assertions.count() == 4

    def test_unicode(self):
        session = Revision.query.session
        r = Revision(message=u'αβγδεζηθικλμνξ', author=u'爆発物持者立入禁止')
        session.add(r)
        session.commit()


class TestAssertionModel(fixtures.BaseCase):

    def test_unicode(self):
        session = Assertion.query.session
        a = Assertion(text=u'αβγδεζηθικλμνξ')
        session.add(a)
        session.commit()
