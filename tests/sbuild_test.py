from nose.tools import *

from debs import cfg, dists, sbuild

# def setup():
# 	sbuild.ensure(
# 		cfg.Cfg(),
# 		'{}-amd64'.format(dists._DEBIAN[0]),
# 		'{}-amd64'.format(dists._DEBIAN[1]))

def test_match():
	assert_greater(len(sbuild.match('amd64', 'blah')), 0)
	assert_greater(len(sbuild.match('blah', 'i386')), 0)
