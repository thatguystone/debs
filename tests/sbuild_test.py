from nose.tools import *
import os

from debs import cfg, dists, package, sbuild

from . import util

_DISTS = [
	'{}-amd64'.format(dists._DEBIAN[0]),
	'{}-amd64'.format(dists._DEBIAN[1]),
]

# def setup():
# 	sbuild.ensure(cfg.Cfg(), *_DISTS)

def test_match():
	assert_greater(len(sbuild.match('amd64', 'blah')), 0)
	assert_greater(len(sbuild.match('blah', 'i386')), 0)

def test_build_native():
	p = util.fixture('pkgs', 'native')
	os.environ['SBUILD_CONFIG'] = util.fixture('pkgs', '.sbuildrc')
	sbuild.build(cfg.Cfg(), package.load(p), _DISTS[0])

def test_build_native_dsc():
	p = util.fixture('pkgs', 'native-dsc', 'native_1.2.3.dsc')
	sbuild.build(cfg.Cfg(), package.load(p), _DISTS[0])

def test_build_quilt():
	p = util.fixture('pkgs', 'quilt')
	sbuild.build(cfg.Cfg(), package.load(p), _DISTS[0])

def test_build_quilt_dsc():
	p = util.fixture('pkgs', 'quilt-dsc', 'quilt_3.2.1-1.dsc')
	sbuild.build(cfg.Cfg(), package.load(p), _DISTS[0])
