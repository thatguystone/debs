from nose.tools import *

from debs import Debs, dists

from . import util

class _Debs(Debs):
	def __init__(self, dists=[], remotes=[], pkgs=[], extra_cfgs=[]):
		super().__init__(
			dists=dists, remotes=remotes,
			pkgs=pkgs, extra_cfgs=extra_cfgs)

		self.cfg.batch = True
		self.cfg.no_versions = True

def test_pkg_expand():
	d = Debs(pkgs=[util.fixture('pkgs', '**/*.dsc')])
	assert_not_equal([], d.pkgs)

def test_pkg_current_directory():
	# Load current directory: should load deb's debian/ dir
	d = Debs()
	assert_equal(1, len(d.pkgs))
	assert_equal('debs', d.pkgs[0].name)

def test_get_dists():
	d = Debs()

	dl = d.get_dists()
	for dist in dists.DISTS:
		assert_in(dist, dl)

def test_get_dists_filter():
	which = [dists.DISTS[0]]
	d = Debs(dists=which)

	dl = d.get_dists()
	assert_equal(which, dl)

def test_get_remotes():
	d = Debs()

	rl = d.get_remotes()
	assert_not_equal([], rl)

def test_build():
	d = _Debs(
		pkgs=[util.fixture('pkgs', 'native')],
		dists=[dists.DISTS[0]])
	d.build()
