import multiprocessing
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

	srcs = set([
		'deb http://testing extras',
		'deb http://testing herp',
		'deb http://testing testing',
	])
	assert_equal(
		srcs,
		c.extra_sources('herp', 'testing').intersection(srcs))

	srcs = set([
		'deb http://debian debian',
		'deb http://testing extras',
	])
	assert_equal(
		srcs,
		c.extra_sources('debian', 'testing').intersection(srcs))

	assert_equal(
		set(['deb http://debian debian']),
		c.extra_sources('debian', 'future release').intersection(srcs))

def test_packages():
	c = cfg.Cfg()
	c.load_string('''
	[debs]
	packages = blerp, merp, gerp
	packages-debian = debian
	packages-jessie = jessie
	''')

	pkgs = set(['blerp', 'merp', 'gerp', 'debian'])
	assert_equal(
		pkgs,
		pkgs.intersection(c.packages('debian', 'sid')))

	pkgs = set(['blerp', 'merp', 'gerp', 'debian', 'jessie'])
	assert_equal(
		pkgs,
		pkgs.intersection(c.packages('debian', 'jessie')))

def test_climb_sources_list():
	c = cfg.Cfg(base=util.fixture('debsrc/subdir'))

	srcs = set([
		'src http://basic extras',
		'src http://quilt extras',
	])

	assert_equal(
		srcs,
		c.extra_sources('debian', 'testing').intersection(srcs))

def test_climb():
	c = cfg.Cfg(base=util.fixture('debsrc/subdir'))
	assert_equal('http://quilt', c.main_mirror('debian', 'testing'))

def test_climb_env():
	c = cfg.Cfg(base=util.fixture('debsrc/subdir'))
	assert_equal('YES', c.env['val'])

def test_in_path():
	c = cfg.Cfg(base=util.fixture('debsrc/'))
	assert_equal(multiprocessing.cpu_count(), c.jobs)

	nc = c.in_path(util.fixture('debsrc/another'))
	assert_equal(123, nc.jobs)

	assert_not_equal(c.c, nc.c)
	assert_not_equal(c.cs, nc.cs)
	assert_not_equal(c.loaded, nc.loaded)
