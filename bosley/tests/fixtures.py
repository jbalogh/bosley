from datetime import datetime

import fixture

# Need to be loaded so the fixture mapper can find them.
from bosley import utils
from bosley.models import Revision, TestFile, Test, Assertion


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


class TestFileData(fixture.DataSet):

    class broken_r1:
        name = 'broken.tests'
        broken = True
        revision = RevisionData.r1

    class database_r1:
        name = 'database.tests'
        revision = RevisionData.r1

    class broken_r2(broken_r1):
        revision = RevisionData.r2

    class database_r2(database_r1):
        revision = RevisionData.r2

    class config_r2(database_r2):
        name = 'config.test'


class TestData(fixture.DataSet):

    class testDefaults_r1:
        name = 'testDefaults'
        testfile = TestFileData.database_r1
        revision = RevisionData.r1

    class testFallback_r1(testDefaults_r1):
        name = 'testFallback'

    class testDefaults_r2(testDefaults_r1):
        testfile = TestFileData.database_r2
        revision = RevisionData.r2

    class testFallback_r2(testFallback_r1):
        testfile = TestFileData.database_r2
        revision = RevisionData.r2

    class testConfig_r2(testFallback_r2):
        testfile = TestFileData.config_r2
        name = 'testConfig'


class AssertionData(fixture.DataSet):

    class default_r1:
        text = u'Default shadow db....'
        fail = False
        test = TestData.testDefaults_r1
        revision = RevisionData.r1

    class fallback_r1(default_r1):
        text = u'Fallback to shadow...'
        test = TestData.testFallback_r1

    class enabled_r1(fallback_r1):
        text = u'Shadow databases are...'
        fail = True

    class disabled_r1(fallback_r1):
        text = u'Disabled shadow databases...'

    class default_r2(default_r1):
        test = TestData.testDefaults_r2
        revision = RevisionData.r2

    class fallback_r2(fallback_r1):
        fail = True
        test = TestData.testFallback_r2
        revision = RevisionData.r2

    class enabled_r2(enabled_r1):
        test = TestData.testFallback_r2
        revision = RevisionData.r2

    class disabled_r2(disabled_r1):
        test = TestData.testFallback_r2
        revision = RevisionData.r2

    class config_r2:
        text = u'Config bla bla...'
        fail = True
        test = TestData.testConfig_r2
        revision = RevisionData.r2


class BaseCase(fixture.DataTestCase):
    fixture = fixture.SQLAlchemyFixture(
        env=globals(),
        style=fixture.TrimmedNameStyle(suffix="Data"),
    )
    datasets = [RevisionData, TestFileData, TestData, AssertionData]

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
