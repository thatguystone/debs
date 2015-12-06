from nose.tools import *

from debs import Debs, envs

from . import util

class _Debs(Debs):
	def __init__(self, envs=[], remotes=[], pkgs=[], extra_cfgs=[]):
		super().__init__(
			envs=envs, remotes=remotes,
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

def test_get_envs():
	d = Debs()

	dl = d.get_envs('all')
	for dist in envs.ENVS:
		assert_in(dist, dl)

def test_get_envs_filter():
	which = [envs.ENVS[0]]
	d = Debs(envs=which)

	dl = d.get_envs()
	assert_equal(which, dl)

def test_get_remotes():
	d = Debs()

	rl = d.get_remotes()
	assert_not_equal([], rl)

def test_build():
	d = _Debs(
		pkgs=[util.fixture('pkgs', 'native')],
		envs=[envs.ENVS[0]])
	d.build()
