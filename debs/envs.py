import itertools

from . import util

_ARCHS = ['amd64', 'i386']

_DEBIAN = [
	'jessie',
	'stretch',
	'sid',
]

_UBUNTU = [
	'precise',
	'trusty',
	'wily',
	'xenial',
]

_ENVS = _DEBIAN + _UBUNTU

ENVS = sorted(['-'.join(c) for c in itertools.product(_ENVS, _ARCHS)])

_COMPONENTS = {
	'debian': (_DEBIAN, 'main contrib non-free'),
	'ubuntu': (_UBUNTU, 'main restricted universe multiverse'),
}

_MIRRORS = {
	'debian': (_DEBIAN, 'http://httpredir.debian.org/debian'),
	'ubuntu': (_UBUNTU, 'http://us.archive.ubuntu.com/ubuntu/'),
}

def split(env):
	return env.split('-')

def match(*specs, installed=None):
	specs = list(filter(None, specs))
	if not specs:
		specs = ['all']

	all = ENVS.copy()
	if installed:
		all += list(installed)

	envs = set()
	for spec in specs:
		if spec == 'all':
			envs.update(all)
		else:
			for e in all:
				if e.startswith(spec) or e.endswith(spec):
					envs.add(e)

	return envs

def main_mirror(release, cfg=None):
	for dist, specs in _MIRRORS.items():
		if release in specs[0]:
			if cfg and cfg.main_mirror(dist, release):
				return cfg.main_mirror(dist, release)

			return specs[1]

	raise UnknownRelease(release)

def packages(release, arch, cfg=None):
	if cfg:
		for dist, specs in _MIRRORS.items():
			if release in specs[0]:
				return cfg.extra_packages(dist, release, arch)

	return set()

def components(release, sep=' '):
	for dist, specs in _COMPONENTS.items():
		if release in specs[0]:
			return specs[1].replace(' ', sep)

	raise UnknownRelease(release)

def sources(release, arch, cfg=None):
	main = main_mirror(release, cfg=cfg)
	comps = components(release)

	srcs = set([
		'deb {} {} {}'.format(main, release, comps).strip(),
		'deb-src {} {} {}'.format(main, release, comps).strip(),
	])

	if cfg and cfg.extra_sources(release, release, arch):
		srcs |= cfg.extra_sources(release, release, arch)

	return '\n'.join(sorted(srcs)) + '\n'

class UnknownRelease(Exception):
	pass
