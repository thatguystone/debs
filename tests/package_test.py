from nose.tools import *

from debs import cfg, package
from . import util

def test_load():
	c = cfg.Cfg()

	p = package.load(util.fixture('pkgs', 'crazy-formatting'), c)
	assert_equal(p.name, 'crazy-formatting')
	assert_equal(p.version, '1.2.3')

	p = package.load(util.fixture('pkgs', 'native'), c)
	assert_equal(p.name, 'native')
	assert_equal(p.version, '1.2.3')

	p = package.load(util.fixture('pkgs', 'quilt'), c)
	assert_equal(p.name, 'quilt')
	assert_equal(p.version, '3.2.1-1')

	with util.tmpdir() as tmpdir:
		dsc_path = util.fixture('pkgs', 'native-dsc', 'native_1.2.3.dsc')
		p = package.load(dsc_path, c)
		assert_equal(p.name, 'native')
		assert_equal(p.version, '1.2.3')
		assert_equal(p.gen_src(tmpdir), dsc_path)

@raises(package.InvalidPackage)
def test_no_format():
	c = cfg.Cfg()
	package.load(util.fixture('errors', 'no-format'), c)

@raises(package.InvalidPackage)
def test_no_control():
	c = cfg.Cfg()
	package.load(util.fixture('errors', 'no-control'), c)

@raises(package.InvalidPackage)
def test_no_changelog():
	c = cfg.Cfg()
	package.load(util.fixture('errors', 'no-changelog'), c)

@raises(package.InvalidPackage)
def test_invalid_changelog():
	c = cfg.Cfg()
	package.load(util.fixture('errors', 'invalid-changelog'), c)

@raises(package.InvalidPackage)
def test_unsupported_type():
	c = cfg.Cfg()
	package.load(util.fixture('errors', 'unsupported-type'), c)
