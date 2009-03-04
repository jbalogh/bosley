import os

from bosley import settings, utils
from bosley.tests import fixtures


def setup_module():
    settings.DATABASE += '.test'
    utils.Session.bind = fixtures.BaseCase.fixture.engine = utils.engine()
    utils.metadata.create_all(utils.Session.bind)


def teardown_module():
    # XXX: only on sqlite
    os.remove(settings.DATABASE.replace('sqlite:///', ''))
    settings.DATABASE.replace('.test', '')
