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

_DISTS = _DEBIAN + _UBUNTU

DISTS = sorted(['-'.join(c) for c in itertools.product(_DISTS, _ARCHS)])

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

	all = DISTS.copy()
	if installed:
		all += list(installed)

	dists = set()
	for spec in specs:
		if spec == 'all':
			dists.update(all)
		else:
			for d in all:
				if d.startswith(spec) or d.endswith(spec):
					dists.add(d)

	return dists

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

def sources(release, arch, cfg=None):
	main = main_mirror(release, cfg=cfg)

	# Don't need an error check for this: release verified in main_mirror()
	for dist, specs in _COMPONENTS.items():
		if release in specs[0]:
			break

	srcs = set([
		'deb {} {} {}'.format(main, release, specs[1]).strip(),
		'deb-src {} {} {}'.format(main, release, specs[1]).strip(),
	])

	if cfg and cfg.extra_sources(dist, release, arch):
		srcs |= cfg.extra_sources(dist, release, arch)

	return '\n'.join(sorted(srcs)) + '\n'

class UnknownRelease(Exception):
	pass
