from nose.tools import *

from debs import cfg

from . import util

def test_overrides():
	c = cfg.Cfg()

	m = 'http://local/mirror'

	c.load_string('''
	[repos]
	debian = nopers
	''')

	c.load_string('''
	[repos]
	debian = {}
	'''.format(m))

	assert_equal(m, c.main_mirror('debian', 'testing'))
	assert_equal(None, c.main_mirror('blerp', 'derp'))

def test_main_mirror():
	c = cfg.Cfg()

	m = 'http://local/mirror'

	c.load_string('''
	[repos]
	debian = nopers
	testing = nopers
	''')

	c.load_string('''
	[repos]
	debian = m-{}
	testing = t-{}
	'''.format(m, m))

	assert_equal('t-'+m, c.main_mirror('herp', 'testing'))
	assert_equal('m-'+m, c.main_mirror('debian', 'doom'))

def test_sources_list():
	c = cfg.Cfg()

	c.load_string('''
	[repos]
	debian = http://debian
	extras-debian = \
		deb http://debian {DIST}

	testing = http://testing
	extras-testing = \
		deb http://testing extras

		deb http://testing {DIST}

		deb http://testing {RELEASE}
	''')

	assert_in(
		'deb http://testing extras\n\n'
		'deb http://testing herp\n\n'
		'deb http://testing testing',
		c.extra_sources('herp', 'testing'))

	assert_in(
		'deb http://debian debian\n'
		'deb http://testing extras',
		c.extra_sources('debian', 'testing'))

	assert_in(
		'deb http://debian debian',
		c.extra_sources('debian', 'future release'))

def test_packages():
	c = cfg.Cfg()
	c.load_string('''
	[debs]
	packages = blerp, merp, gerp
	packages-debian = debian
	packages-jessie = jessie
	''')

	assert_equal(
		set(['blerp', 'merp', 'gerp', 'debian']),
		c.packages('debian', 'sid'))

	assert_equal(
		set(['blerp', 'merp', 'gerp', 'debian', 'jessie']),
		c.packages('debian', 'jessie'))

def test_climb_sources_list():
	c = cfg.Cfg(base=util.fixture('basic/quilt'))
	assert_in(
		'src http://basic extras\n'
		'src http://quilt extras',
		c.extra_sources('debian', 'testing'))

def test_climb():
	c = cfg.Cfg(base=util.fixture('basic/quilt'))
	assert_equal('http://quilt', c.main_mirror('debian', 'testing'))
