from datetime import datetime

import fixture

# Need to be loaded so the fixture mapper can find them.
from bosley.models import Result, Revision, Case, TestFile, Test, Assertion


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


class CaseData(fixture.DataSet):

    class failing:
        name = 'failing case'

    class broken:
        name = 'broken case'


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
        case = CaseData.failing

    class broken(passing1):
        broken = True
        passes = fails = 0
        case = CaseData.broken

    class passing_r2(passing1):
        revision = RevisionData.r2


class TestFileData(fixture.DataSet):

    class broken:
        name = 'broken.tests'
        broken = True
        revision = RevisionData.r1

    class database:
        name = 'database.tests'
        revision = RevisionData.r1


class TestData(fixture.DataSet):

    class testDefaults:
        name = 'testDefaults'
        testfile = TestFileData.database
        revision = RevisionData.r1

    class testPopulated(testDefaults):
        name = 'testPopulated'

    class testFallback(testDefaults):
        name = 'testFallback'

    class testNoErrors(testDefaults):
        name = 'testNoErrors'


class AssertionData(fixture.DataSet):

    class default:
        text = 'Default shadow db....'
        fail = False
        test = TestData.testDefaults
        revision = RevisionData.r1

    class populated(default):
        text = 'Populated shadow db...'
        test = TestData.testPopulated

    class fallback(default):
        text = 'Fallback to shadow...'
        test = TestData.testFallback

    class enabled(fallback):
        text = 'Shadow databases are...'
        fail = True

    class disabled(fallback):
        text = 'Disabled shadow databases...'

    class noerror(default):
        text = 'Should be no...'
        test = TestData.testNoErrors


class BaseCase(fixture.DataTestCase):
    fixture = fixture.SQLAlchemyFixture(
        env=globals(),
        style=fixture.TrimmedNameStyle(suffix="Data"),
    )
    datasets = [RevisionData, ResultData, CaseData,
                TestFileData, TestData, AssertionData,
                ]
