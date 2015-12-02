import configparser
import copy
import io
import multiprocessing
import os
import os.path
import shlex

from . import util

DEFAULTS = [
	'/etc/debsrc',
	'~/.debsrc',
]

GROUP = 'debs'
REPOS = 'repos'
SBUILD = 'sbuild'

class Cfg(object):
	def __init__(self, base=os.getcwd(), load=True):
		self.c = configparser.ConfigParser()
		self.cs = []
		self.loaded = set()

		if not load:
			return

		for f in DEFAULTS:
			self._load(f)

		self._load_tree(base)

	def _load_tree(self, base):
		paths = []
		curr = base
		while curr != '/':
			paths.insert(0, os.path.join(curr, '.debsrc'))
			curr = os.path.dirname(curr)

		for p in paths:
			self._load(p)

	def _load(self, f):
		if not os.path.exists(f) or f in self.loaded:
			return

		self.loaded.add(f)
		self.c.read(f)

		c = configparser.ConfigParser()
		c.read(f)
		self.cs.append(c)

	def _get_all(self, group, key, fallback=None):
		res = []
		for c in self.cs:
			v = c.get(group, key, fallback=fallback)
			if v:
				res.append(v)

		return res

	def in_path(self, path):
		"""
		Get a new config object with any extra .debsrc files loaded from the
		given path and its parents.
		"""

		cfg = Cfg(load=False)
		cfg.cs = copy.copy(self.cs)
		cfg.loaded = copy.copy(self.loaded)

		f = io.StringIO()
		self.c.write(f)
		cfg.load_string(f.getvalue())

		cfg._load_tree(path)

		return cfg

	def load_string(self, str):
		self.c.read_string(str)

		c = configparser.ConfigParser()
		c.read_string(str)
		self.cs.append(c)

	def main_mirror(self, dist, release):
		v = self.c.get(REPOS, release, fallback=None)
		if not v:
			v = self.c.get(REPOS, dist, fallback=None)

		return v

	def extra_sources(self, dist, release):
		srcs = ''

		vs = [
			self._get_all(REPOS, 'extras-' + dist, fallback=None),
			self._get_all(REPOS, 'extras-' + release, fallback=None),
		]
		for v in vs:
			if v:
				srcs += '\n'.join(v)
				srcs += '\n'

		srcs = srcs.format(
			DIST=dist,
			RELEASE=release)

		return util.to_set(srcs.split('\n'))

	def packages(self, dist, release):
		pkgs = []

		vs = [
			self._get_all(GROUP, 'packages', fallback=None),
			self._get_all(GROUP, 'packages-' + dist, fallback=None),
			self._get_all(GROUP, 'packages-' + release, fallback=None),
		]

		for v in vs:
			for p in v:
				pkgs += map(lambda s: s.strip(), p.split(','))

		return set(filter(None, pkgs))

	@property
	def refresh_after(self):
		return self.c.get(GROUP, 'refresh-after', fallback=60*60*24*7)

	@property
	def jobs(self):
		return self.c.getint(SBUILD, 'jobs', fallback=multiprocessing.cpu_count())

	@property
	def key(self):
		return self.c.get(SBUILD, 'key', fallback=None)

	@property
	def lintian(self):
		return self.c.getboolean(SBUILD, 'lintian', fallback=True)

	@property
	def lintian_args(self):
		return shlex.split(self.c.get(SBUILD, 'lintian-args', fallback='-i -I'))

	@property
	def apt_upgrade(self):
		return self.c.getboolean(SBUILD, 'apt-upgrade', fallback=True)

	@property
	def dry_run(self):
		return self.c.getboolean(SBUILD, 'dry-run', fallback=False)

	@property
	def env(self):
		env = {}
		for c in self.cs:
			if c.has_section('env'):
				env.update(dict(c.items('env')))

		return env

class ConfigException(Exception):
	pass
