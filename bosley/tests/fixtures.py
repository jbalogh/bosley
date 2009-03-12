from datetime import datetime

import fixture

# Need to be loaded so the fixture mapper can find them.
from bosley import utils
from bosley.models import Result, Revision, Case, TestFile, Test, Assertion


class RevisionData(fixture.DataSet):

    class r1:
        svn_id = 1
        git_id = '1' * 40
        message = u'bla'
        author = u'jeff'
        date = datetime(2009, 03, 01)

    class r2:
        svn_id = 2
        git_id = '2' * 40
        message = u'foo'
        author = u'fred'
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
        text = u'Default shadow db....'
        fail = False
        test = TestData.testDefaults
        revision = RevisionData.r1

    class populated(default):
        text = u'Populated shadow db...'
        test = TestData.testPopulated

    class fallback(default):
        text = u'Fallback to shadow...'
        test = TestData.testFallback

    class enabled(fallback):
        text = u'Shadow databases are...'
        fail = True

    class disabled(fallback):
        text = u'Disabled shadow databases...'

    class noerror(default):
        text = u'Should be no...'
        test = TestData.testNoErrors


class BaseCase(fixture.DataTestCase):
    fixture = fixture.SQLAlchemyFixture(
        env=globals(),
        style=fixture.TrimmedNameStyle(suffix="Data"),
    )
    datasets = [RevisionData, ResultData, CaseData,
                TestFileData, TestData, AssertionData,
                ]

    def setup(self):
        utils.metadata.drop_all(utils.Session.bind)
        utils.metadata.create_all(utils.Session.bind)
        fixture.DataTestCase.setUp(self)


testcase_xml = """
<?xml version="1.0"?>
<run>
  <group size="2">
    <name>Test Case: database.test.php</name>
    <group size="1">
      <name>/bot/amo/site/app/tests/database.test.php</name>
      <case>
        <name>DatabaseTest</name>
        <test>
          <name>testDefaults</name>
          <pass>Default shadow db config does not cause SHADOW constants to be set at [/bot/amo/site/app/tests/database.test.php line 79]</pass>
        </test>
        <test>
          <name>testPopulated</name>
          <pass>Populated shadow db config returns 1 database at [/bot/amo/site/app/tests/database.test.php line 85]</pass>
        </test>
        <test>
          <name>testFallback</name>
          <pass>Fallback to shadow database 2 when shadow database 1 is down at [/bot/amo/site/app/tests/database.test.php line 109]</pass>
          <fail>Shadow databases are still enabled at [/bot/amo/site/app/tests/database.test.php line 110]</fail>
          <pass>Disabled shadow databases because all shadows are down at [/bot/amo/site/app/tests/database.test.php line 124]</pass>
        </test>
      </case>
    </group>
    <group size="1">
      <name>/bot/amo/site/app/tests/global.test.php</name>
      <case>
        <name>GlobalTest</name>
        <test>
          <name>testNoErrors</name>
          <pass>Should be no errors at [/bot/amo/site/app/tests/global.test.php line 46]</pass>
        </test>
      </case>
    </group>
  </group>
</run>
"""

discover_xml = """
<?xml version="1.0" ?>
<cases>
  <case>app_controller.test.php</case>
  <case>controllers/addons_controller.test.php</case>
</cases>
"""
