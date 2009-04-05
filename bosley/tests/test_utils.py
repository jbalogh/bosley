from bosley import utils

def test_perlsub():
    assert utils.perlsub('foobar', '(foo)(bar)', '$2$1') == 'barfoo'
