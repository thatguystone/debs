import itertools

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

DISTS = ['-'.join(c) for c in itertools.product(_DISTS, _ARCHS)]

_COMPONENTS = {
	'debian': (_DEBIAN, 'main contrib non-free'),
	'ubuntu': (_UBUNTU, 'main restricted universe multiverse'),
}

_MIRRORS = {
	'debian': (_DEBIAN, 'http://httpredir.debian.org/debian'),
	'ubuntu': (_UBUNTU, 'http://us.archive.ubuntu.com/ubuntu/'),
}

def match(*specs, installed=None):
	specs = list(filter(None, specs))
	if not specs:
		return []

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

def packages(release, cfg=None):
	if cfg:
		for dist, specs in _MIRRORS.items():
			if release in specs[0]:
				return cfg.packages(dist, release)

	return set()

def sources(release, cfg=None):
	main = main_mirror(release, cfg=cfg)

	# Don't need an error check for this: release verified in main_mirror()
	for dist, specs in _COMPONENTS.items():
		if release in specs[0]:
			break

	srcs = 'deb {} {} {}\n'.format(main, release, specs[1])
	srcs += 'deb-src {} {} {}\n'.format(main, release, specs[1])

	if cfg and cfg.extra_sources(dist, release):
		srcs += cfg.extra_sources(dist, release)

	return srcs.strip() + '\n'

class UnknownRelease(Exception):
	pass
