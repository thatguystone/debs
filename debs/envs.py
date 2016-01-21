import itertools
import json
import os
import re
import time
import urllib.request

from . import consts, util

_ARCHS = ['amd64', 'i386']

_DEBIAN = []
_UBUNTU = []
_ENVS = []

_COMPONENTS = {
	'debian': (_DEBIAN, 'main contrib non-free'),
	'ubuntu': (_UBUNTU, 'main restricted universe multiverse'),
}

_MIRRORS = {
	'debian': (_DEBIAN, 'http://httpredir.debian.org/debian'),
	'ubuntu': (_UBUNTU, 'http://us.archive.ubuntu.com/ubuntu/'),
}

_ALIASES = {}
ENVS = []

def _load_releases():
	os.makedirs(consts.CFG_DIR, exist_ok=True)
	releases = os.path.join(consts.CFG_DIR, 'releases')

	refresh = True
	if os.path.exists(releases):
		age = time.time() - os.path.getmtime(releases)
		if age < 60*60*24*7:
			refresh = False
			with open(releases) as f:
				all = json.load(f)

	if refresh:
		all = _refresh_releases(releases)

	_DEBIAN.extend(all['debian'])
	_UBUNTU.extend(all['ubuntu'])
	_ALIASES.update(all['aliases'])
	_ENVS.extend(_DEBIAN + _UBUNTU + list(_ALIASES.keys()))
	ENVS.extend(sorted(['-'.join(c) for c in itertools.product(_ENVS, _ARCHS)]))

def _refresh_releases(path):
	aliases = {}
	debian = []
	ubuntu = []
	_refresh_debian_releases(aliases, debian)
	_refresh_ubuntu_releases(aliases, ubuntu)

	all = {
		'debian': list(map(lambda r: r.lower(), debian)),
		'ubuntu': list(map(lambda r: r.lower(), ubuntu)),
		'aliases': dict(map(lambda kv: (kv[0], kv[1].lower()), aliases.items())),
	}
	with open(path, 'w') as f:
		json.dump(all, f, indent=4, sort_keys=True)

	return all

def _refresh_debian_releases(aliases, rels):
	r = re.compile(r'Debian &ldquo;(\w*)&rdquo;')
	def get(which):
		url = 'https://www.debian.org/releases/{}/'.format(which)
		s = urllib.request.urlopen(url).read()
		return r.findall(s.decode('utf-8'))[0]

	stable = aliases['debian-stable'] = get('stable')
	testing = aliases['debian-testing'] = get('testing')
	unstable = aliases['debian-unstable'] = 'sid'

	rels += [stable, testing, unstable]

def _refresh_ubuntu_releases(aliases, rels):
	rel = urllib.request.urlopen('http://releases.ubuntu.com/').read()
	all = re.findall(r'Ubuntu ([\d\.]*) (.*)\((\w*) \w*\)', rel.decode('utf-8'))
	all = sorted(set(all), reverse=True)

	aliases['ubuntu-latest'] = all[0][2]
	aliases['ubuntu-lts'] = next((r[2] for r in all if 'lts' in r[1].lower()))

	rels += map(lambda r: r[2], all)

def split(env):
	parts = env.rsplit('-', 1)
	if parts and '-' in parts[0]:
		parts[0] = _ALIASES.get(parts[0], parts[0])
	return parts

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

	return sorted(envs)

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

def dist(release):
	for dist, specs in _COMPONENTS.items():
		if release in specs[0]:
			return dist

	raise UnknownRelease(release)

def sources(release, arch, cfg=None):
	main = main_mirror(release, cfg=cfg)
	comps = components(release)
	d = dist(release)

	srcs = set([
		'deb {} {} {}'.format(main, release, comps).strip(),
		'deb-src {} {} {}'.format(main, release, comps).strip(),
	])

	if cfg and cfg.extra_sources(d, release, arch):
		srcs |= cfg.extra_sources(d, release, arch)

	return '\n'.join(sorted(srcs)) + '\n'

class UnknownRelease(Exception):
	pass

_load_releases()
