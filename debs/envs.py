import ftplib
import inspect
import itertools
import json
import logging
import os
import re
import time
import urllib.request

import debian.deb822

from . import cfg, util

log = logging.getLogger(__name__)

def split(env):
	parts = env.rsplit('-', 1)
	if parts and '-' in parts[0]:
		parts[0] = ENVS.ALIASES.get(parts[0], parts[0])
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
	for dist, specs in ENVS.MIRRORS.items():
		if release in specs[0]:
			if cfg and cfg.main_mirror(dist, release):
				return cfg.main_mirror(dist, release)

			return specs[1]

	raise UnknownRelease(release)

def packages(release, arch, cfg=None):
	if cfg:
		for dist, specs in ENVS.MIRRORS.items():
			if release in specs[0]:
				return cfg.extra_packages(dist, release, arch)

	return set()

def components(release, sep=' '):
	for dist, specs in ENVS.COMPONENTS.items():
		if release in specs[0]:
			return specs[1].replace(' ', sep)

	raise UnknownRelease(release)

def dist(release):
	for dist, specs in ENVS.COMPONENTS.items():
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

class _Envs(list):
	_ARCHS = ['amd64', 'i386']

	_ALIASES = {}

	_DEBIAN_ALIASES = ['stable', 'testing', 'unstable']

	_DEBIAN = []
	_UBUNTU = []

	_COMPONENTS = {
		'debian': (_DEBIAN, 'main contrib non-free'),
		'ubuntu': (_UBUNTU, 'main restricted universe multiverse'),
	}

	_MIRRORS = {
		'debian': (_DEBIAN, 'http://httpredir.debian.org/debian'),
		'ubuntu': (_UBUNTU, 'http://us.archive.ubuntu.com/ubuntu/'),
	}

	def __init__(self):
		self._loaded = False

		ms = inspect.getmembers(self, lambda a: not inspect.isroutine(a))
		for m in ms:
			n = m[0]
			if n.upper() == n:
				setattr(_Envs, n[1:], property(self._getter(n)))

	def _getter(self, n):
		def fn(self):
			self._load()
			return getattr(self, n)
		return fn

	def _should_refresh(self, path):
		try:
			mod = os.path.getmtime(path)
			return mod <= (time.time() - (86400 * 7))
		except os.error:
			return True

	def _load_debian(self):
		path = os.path.join(cfg.cfg_dir(), 'debian.release')
		if self._should_refresh(path):
			self._refresh_debian(path)

		with open(path, 'r') as f:
			dists = json.load(f)

		for a in self._DEBIAN_ALIASES:
			self._ALIASES['debian-{}'.format(a)] = dists[a]
			self._DEBIAN.append(dists[a])

	def _refresh_debian(self, path):
		log.info('refreshing Debian releases...')

		lines = []
		with ftplib.FTP('ftp.us.debian.org') as ftp:
			ftp.login()
			ftp.cwd('debian/dists/')
			ftp.retrlines('LIST', callback=lambda l: lines.append(l))

		dists = {}
		for l in lines:
			if '->' in l:
				sl = l.split()
				dists[sl[-3]] = sl[-1]

		dists = {a: dists[a] for a in self._DEBIAN_ALIASES}
		with open(path, 'w') as f:
			json.dump(dists, f)

	def _load_ubuntu(self):
		path = os.path.join(cfg.cfg_dir(), 'ubuntu.release')
		if self._should_refresh(path):
			self._refresh_ubuntu(path)

		with open(path, 'r') as f:
			rels = json.load(f)

		self._ALIASES['ubuntu-latest'] = rels['latest']
		self._ALIASES['ubuntu-lts'] = rels['lts']

		self._UBUNTU += rels['vers']

	def _refresh_ubuntu(self, path):
		log.info('refreshing Ubuntu releases...')

		rels = {
			'vers': [],
		}

		resp = urllib.request.urlopen('http://changelogs.ubuntu.com/meta-release')
		for p in debian.deb822.Deb822.iter_paragraphs(resp):
			if p['Supported'] != '1':
				continue

			dist = p['Dist']

			rels['latest'] = dist
			if 'LTS' in p['Version']:
				rels['lts'] = dist

			rels['vers'].append(dist)

		with open(path, 'w') as f:
			json.dump(rels, f)

	def _load(self):
		if self._loaded:
			return

		self._load_debian()
		self._load_ubuntu()
		self._ENVS = self._DEBIAN + self._UBUNTU + list(self._ALIASES.keys())
		self += sorted(['-'.join(c) for c in itertools.product(self._ENVS, self._ARCHS)])
		self._loaded = True

	def copy(self):
		self._load()
		return super().copy()

	def __getitem__(self, *args, **kwargs):
		self._load()
		return super().__getitem__(*args, **kwargs)

	def __iter__(self):
		self._load()
		return super().__iter__()

	def __len__(self):
		self._load()
		return super().__len__()

ENVS = _Envs()
