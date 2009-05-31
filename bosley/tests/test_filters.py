from bosley import filters


def test_perlsub():
    assert filters.perlsub('foobar', '(foo)(bar)', '$2x$1') == 'barxfoo'
