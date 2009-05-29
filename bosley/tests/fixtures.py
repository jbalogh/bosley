from datetime import datetime

import fixture

# Need to be loaded so the fixture mapper can find them.
from bosley import utils
from bosley.models import (Revision, TestFile, Test,
                           Assertion, BrokenTest, Result)


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

    class broken:
        name = 'broken.tests'

    class database:
        name = 'database.tests'

    class config:
        name = 'config.test'


class TestData(fixture.DataSet):

    class testDefaults:
        name = 'testDefaults'
        testfile = TestFileData.database

    class testFallback(testDefaults):
        name = 'testFallback'

    class testConfig:
        testfile = TestFileData.config
        name = 'testConfig'

    # Same test name, different file.
    class testFallbackInConfig:
        name = 'testFallback'
        testfile = TestFileData.config


class AssertionData(fixture.DataSet):

    class default:
        text = u'Default shadow db....'
        test = TestData.testDefaults

    class fallback:
        text = u'Fallback to shadow...'
        test = TestData.testFallback

    class enabled(fallback):
        text = u'Shadow databases are...'
        test = TestData.testFallback

    class disabled:
        text = u'Disabled shadow databases...'
        test = TestData.testFallback

    class config:
        text = u'Config bla bla...'
        test = TestData.testConfig

    class fallbackInConfig:
        text = u'Same test name, different file'
        test = TestData.testFallbackInConfig


class BrokenTestData(fixture.DataSet):

    class broken_r1:
        revision = RevisionData.r1
        testfile = TestFileData.broken

    class broken_r2:
        revision = RevisionData.r2
        testfile = TestFileData.broken


class ResultData(fixture.DataSet):

    class default_r1:
        fail = False
        assertion = AssertionData.default
        revision = RevisionData.r1

    class fallback_r1(default_r1):
        fail = False
        assertion = AssertionData.fallback

    class disabled_r1(default_r1):
        assertion = AssertionData.disabled
        assertion = AssertionData.fallback
        fail = False

    class enabled_r1(default_r1):
        fail = True
        assertion = AssertionData.enabled

    class default_r2(default_r1):
        revision = RevisionData.r2

    class fallback_r2(fallback_r1):
        revision = RevisionData.r2
        fail = True

    class enabled_r2(enabled_r1):
        revision = RevisionData.r2

    class disabled_r2(disabled_r1):
        revision = RevisionData.r2

    class config_r2(fallback_r2):
        fail = True
        assertion = AssertionData.config

    class config_fallback_r2(config_r2):
        fail = True
        assertion = AssertionData.fallbackInConfig


class BaseCase(fixture.DataTestCase):
    fixture = fixture.SQLAlchemyFixture(
        env=globals(),
        style=fixture.TrimmedNameStyle(suffix="Data"),
    )
    datasets = [RevisionData, TestFileData, TestData, AssertionData,
                ResultData, BrokenTestData]

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
