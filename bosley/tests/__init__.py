from bosley import settings, utils
from bosley.tests import fixtures


def setup_module():
    settings.DATABASE = 'sqlite:///:memory:'
    utils.Session.bind = fixtures.BaseCase.fixture.engine = utils.engine()
