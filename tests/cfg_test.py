import multiprocessing
from nose.tools import *
import os.path

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

	extra-all = deb http://1234 all

	extra-debian = \
		deb http://debian {DIST}
	extra-debian-amd64 = \
		deb http://debamd64 {DIST}
	extra-debian-i386 = \
		deb http://debi386 {DIST}

	testing = http://testing
	extra-testing = \
		deb http://testing extras

		deb http://testing {DIST}

		deb http://testing {RELEASE}
	extra-testing-i386 = \
		deb http://testingi386 {RELEASE}
	''')

	srcs = set([
		'deb http://1234 all',
		'deb http://testing extras',
		'deb http://testing herp',
		'deb http://testing testing',
	])
	assert_equal(
		srcs,
		c.extra_sources('herp', 'testing', 'amd64') & srcs)

	srcs = set([
		'deb http://1234 all',
		'deb http://debian debian',
		'deb http://debamd64 debian',
		'deb http://testing extras',
	])
	assert_equal(
		srcs,
		c.extra_sources('debian', 'testing', 'amd64') & srcs)

	srcs = set([
		'deb http://1234 all',
		'deb http://debamd64 debian',
		'deb http://debian debian',
	])
	assert_equal(
		srcs,
		c.extra_sources('debian', 'future release', 'amd64') & srcs)

	srcs = set([
		'deb http://1234 all',
		'deb http://debi386 debian',
	])
	assert_equal(
		srcs,
		c.extra_sources('debian', 'future release', 'i386') & srcs)

def test_packages():
	c = cfg.Cfg()
	c.load_string('''
	[packages]
	all = blerp, merp, gerp
	debian = debian
	debian-i386 = debi386
	debian-amd64 = debamd64
	jessie = jessie
	jessie-i386 = jessi386
	''')

	pkgs = set(['blerp', 'merp', 'gerp', 'debian'])
	assert_equal(
		pkgs,
		pkgs.intersection(c.extra_packages('debian', 'sid', 'amd64')))

	pkgs = set(['blerp', 'merp', 'gerp', 'debian', 'jessie'])
	assert_equal(
		pkgs,
		pkgs.intersection(c.extra_packages('debian', 'jessie', 'amd64')))

	pkgs = set(['blerp', 'merp', 'gerp', 'debian', 'jessie', 'debi386', 'jessi386'])
	assert_equal(
		pkgs,
		pkgs.intersection(c.extra_packages('debian', 'jessie', 'i386')))

	pkgs = set(['blerp', 'merp', 'gerp', 'debian', 'jessie', 'debamd64'])
	assert_equal(
		pkgs,
		pkgs.intersection(c.extra_packages('debian', 'jessie', 'amd64')))

def test_climb_sources_list():
	c = cfg.Cfg(base=util.fixture('debsrc/subdir'))

	srcs = set([
		'src http://basic extras',
		'src http://quilt extras',
	])

	assert_equal(
		srcs,
		c.extra_sources('debian', 'testing', 'amd64') & srcs)

def test_climb():
	c = cfg.Cfg(base=util.fixture('debsrc/subdir'))
	assert_equal('http://quilt', c.main_mirror('debian', 'testing'))

def test_in_path():
	c = cfg.Cfg(base=util.fixture('debsrc/'))
	assert_equal(multiprocessing.cpu_count(), c.jobs)

	nc = c.in_path(util.fixture('debsrc/another'))
	assert_equal(123, nc.jobs)

	assert_not_equal(c._c, nc._c)
	assert_not_equal(c._cs, nc._cs)
	assert_not_equal(c._loaded, nc._loaded)

def test_override():
	c = cfg.Cfg()

	c.lintian_args = '-m -j -k'
	assert_equal(['-m', '-j', '-k'], c.lintian_args)

def test_all_pkgs():
	c = cfg.Cfg(base=util.fixture('debsrc-pkgs/'))

	pkgs = []
	for pc, pkg in c.all_pkgs():
		pkgs.append(os.path.relpath(pkg))

	exp = [
		'tests/fixtures/debsrc-pkgs/pkg0',
		'tests/fixtures/debsrc-pkgs/subs/deeper/quilt0',
		'tests/fixtures/debsrc-pkgs/subs/deeper/quilt1',
		'tests/fixtures/debsrc-pkgs/subs/dsc/test.dsc',
		'tests/fixtures/debsrc-pkgs/subs/native',
	]
	assert_equal(exp, pkgs)
