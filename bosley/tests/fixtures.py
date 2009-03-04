from datetime import datetime

import fixture

from bosley.models import Result, Revision


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

    class passing_r2(passing1):
        revision = RevisionData.r2


class BaseCase(fixture.DataTestCase):
    fixture = fixture.SQLAlchemyFixture(
        env={'ResultData': Result, 'RevisionData': Revision},
    )
    datasets = [RevisionData, ResultData]
