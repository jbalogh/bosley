from bosley.models import Result, Revision
from bosley.tests import fixtures


class TestResultModel(fixtures.BaseCase):

    def test_query(self):
        assert Result.query.filter_by(broken=True).count() == 1


class TestRevisionModel(fixtures.BaseCase):

    def test_results(self):
        rev = Revision.query.filter_by(svn_id=1).one()
        assert rev.results.count() == 4

    def test_stats(self):
        rev = Revision.query.filter_by(svn_id=1).one()
        stats = rev.stats()
        assert stats['broken'] == 1
        assert stats['failing'] == 1
        assert stats['passes'] == 42
        assert stats['fails'] == 2
        assert stats['total'] == 44
