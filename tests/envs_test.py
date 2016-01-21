from nose.tools import *

from debs import cfg, envs

def test_split():
	parts = envs.split('debian-unstable-amd64')
	assert_equal(['sid', 'amd64'], parts)

	parts = envs.split('debian-stable-amd64')
	assert_equal([envs._DEBIAN[0], 'amd64'], parts)

def test_match():
	ds = envs.match('')
	assert_equal(len(envs.ENVS), len(ds))

	ds = envs.match('all')
	assert_not_equal(0, len(ds))

	ds = envs.match('-amd64')
	assert_in('sid-amd64', ds)
	assert_not_in('sid-i386', ds)

	ds = envs.match('sid-')
	assert_in('sid-amd64', ds)
	assert_in('sid-i386', ds)
	assert_not_in(envs._ENVS[0], ds)

	ds = envs.match('test-amd64', installed=['test-amd64'])
	assert_in('test-amd64', ds)

def test_match_aliases():
	ds = envs.match('debian-unstable')
	assert_in('debian-unstable-amd64', ds)

	ds = envs.match('ubuntu-latest')
	assert_in('ubuntu-latest-amd64', ds)

def test_main_mirror():
	c = cfg.Cfg()
	c.load_string('''
	[repos]
	debian = http://debian
	extra-debian = \
		deb http://debian extras

	sid = http://sid
	extra-sid = \
		deb http://sid extras
	''')

	assert_equal('http://sid', envs.main_mirror('sid', cfg=c))
	assert_equal('http://debian', envs.main_mirror(envs._DEBIAN[0], cfg=c))
	assert_equal(envs._MIRRORS['debian'][1], envs.main_mirror(envs._DEBIAN[0]))

@raises(envs.UnknownRelease)
def test_main_mirror_error():
	envs.main_mirror('NONE')

def test_packages():
	assert_equal(set(), envs.packages('jessie', 'amd64'))

	c = cfg.Cfg()
	c.load_string('''
	[packages]
	all = blerp, merp, gerp
	debian = debian
	jessie = jessie
	''')

	pkgs = set(['blerp', 'merp', 'gerp', 'debian', 'jessie'])
	assert_equal(
		pkgs,
		pkgs.intersection(envs.packages('jessie', 'amd64', cfg=c)))

def test_sources():
	c = cfg.Cfg()
	c.load_string('''
	[repos]
	debian = http://debian
	extra-debian = \
		deb http://debian extras

	sid = http://sid
	extra-sid = \
		deb http://sid extras
	''')

	srcs = envs.sources('sid', 'amd64', cfg=c)
	has = [
		'deb http://sid sid main contrib non-free\n',
		'deb-src http://sid sid main contrib non-free\n',
		'deb http://debian extras\n',
		'deb http://sid extras\n',
	]

	for h in has:
		assert_in(h, srcs)

@raises(envs.UnknownRelease)
def test_sources_error():
	envs.sources('NONE', 'i387')
