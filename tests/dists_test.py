from nose.tools import *

from debs import cfg, dists

def test_match():
	ds = dists.match('')
	assert_equal(len(dists.DISTS), len(ds))

	ds = dists.match('all')
	assert_not_equal(0, len(ds))

	ds = dists.match('-amd64')
	assert_in('sid-amd64', ds)
	assert_not_in('sid-i386', ds)

	ds = dists.match('sid-')
	assert_in('sid-amd64', ds)
	assert_in('sid-i386', ds)
	assert_not_in(dists._DISTS[0], ds)

	ds = dists.match('test-amd64', installed=['test-amd64'])
	assert_in('test-amd64', ds)

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

	assert_equal('http://sid', dists.main_mirror('sid', cfg=c))
	assert_equal('http://debian', dists.main_mirror(dists._DEBIAN[0], cfg=c))
	assert_equal(dists._MIRRORS['debian'][1], dists.main_mirror(dists._DEBIAN[0]))

@raises(dists.UnknownRelease)
def test_main_mirror_error():
	dists.main_mirror('NONE')

def test_packages():
	assert_equal(set(), dists.packages('jessie', 'amd64'))

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
		pkgs.intersection(dists.packages('jessie', 'amd64', cfg=c)))

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

	srcs = dists.sources('sid', 'amd64', cfg=c)
	has = [
		'deb http://sid sid main contrib non-free\n',
		'deb-src http://sid sid main contrib non-free\n',
		'deb http://debian extras\n',
		'deb http://sid extras\n',
	]

	for h in has:
		assert_in(h, srcs)

@raises(dists.UnknownRelease)
def test_sources_error():
	dists.sources('NONE', 'i387')
