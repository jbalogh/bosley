from datetime import datetime

import fixture

from bosley import utils
from bosley.models import Result, Revision

engine = utils.Session.bind
utils.metadata.create_all(engine)


model_fixture = fixture.SQLAlchemyFixture(
    env={'ResultData': Result, 'RevisionData': Revision},
    engine=engine,
)


class RevisionData(fixture.DataSet):

    class r1:
        svn_id = 1
        git_id = '1' * 40
        message = 'bla'
        author = 'jeff'
        date = datetime(2009, 03, 01)

    class r2:
        svn_id = 2
        git_id = '2' * 40
        message = 'foo'
        author = 'fred'
        date = datetime(2009, 03, 02)


class ResultData(fixture.DataSet):

    # Inheriting to get the revision object.

    class passing1:
        revision = RevisionData.r1
        passes = 22
        fails = 0

    class passing2(passing1):
        passes = 13
        fails = 0

    class failing(passing1):
        passes = 7
        fails = 2

    class broken(passing1):
        broken = True
        passes = fails = 0


def test_db():
    assert str(engine.url) == 'sqlite:///:memory:'


class TestCaseBase(fixture.DataTestCase):
    fixture = model_fixture
    datasets = [RevisionData, ResultData]


class TestResultModel(TestCaseBase):

    def test_query(self):
        assert Result.query.filter_by(broken=True).count() == 1


class TestRevisionModel(TestCaseBase):

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
