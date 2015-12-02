from nose.tools import *

from debs import package
from . import util

def test_load():
	p = package.load(util.fixture('pkgs', 'crazy-formatting'))
	assert_equal(p.name, 'crazy-formatting')
	assert_equal(p.version, '1.2.3')

	p = package.load(util.fixture('pkgs', 'native'))
	assert_equal(p.name, 'native')
	assert_equal(p.version, '1.2.3')

	p = package.load(util.fixture('pkgs', 'quilt'))
	assert_equal(p.name, 'quilt')
	assert_equal(p.version, '3.2.1-1')

	p = package.load(util.fixture('pkgs', 'native-dsc', 'native_1.2.3.dsc'))
	assert_equal(p.name, 'native')
	assert_equal(p.version, '1.2.3')

@raises(package.InvalidPackage)
def test_no_format():
	package.load(util.fixture('errors', 'no-format'))

@raises(package.InvalidPackage)
def test_no_control():
	package.load(util.fixture('errors', 'no-control'))

@raises(package.InvalidPackage)
def test_no_changelog():
	package.load(util.fixture('errors', 'no-changelog'))

@raises(package.InvalidPackage)
def test_invalid_changelog():
	package.load(util.fixture('errors', 'invalid-changelog'))

@raises(package.InvalidPackage)
def test_unsupported_type():
	package.load(util.fixture('errors', 'unsupported-type'))
