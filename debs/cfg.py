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
	'~/.debs/debsrc',
]

GROUP = 'debs'
PACKAGES = 'packages'
REPOS = 'repos'
SBUILD = 'sbuild'

PROPS = [
	{
		'name': 'refresh-after',
		'type': int,
		'group': GROUP,
		'default': 60*60*24*7,
	},
	{
		'name': 'packages',
		'type': set,
		'group': GROUP,
		'default': '.',
	},
	{
		'name': 'no-versions',
		'type': bool,
		'group': GROUP,
		'default': False,
	},
	{
		'name': 'batch',
		'type': bool,
		'group': GROUP,
		'default': False,
	},
	{
		'name': 'envs',
		'type': set,
		'group': GROUP,
		'default': 'all',
	},
	{
		'name': 'remotes',
		'type': set,
		'group': GROUP,
		'default': 'default',
	},
	{
		'name': 'jobs',
		'type': int,
		'group': SBUILD,
		'default': multiprocessing.cpu_count(),
	},
	{
		'name': 'include-src',
		'type': bool,
		'group': SBUILD,
		'default': True,
	},
	{
		'name': 'user',
		'group': SBUILD,
		'default': None,
	},
	{
		'name': 'user-keep-env',
		'group': SBUILD,
		'default': False,
	},
	{
		'name': 'key',
		'group': SBUILD,
		'default': None,
	},
	{
		'name': 'lintian',
		'type': bool,
		'group': SBUILD,
		'default': True,
	},
	{
		'name': 'lintian-args',
		'group': SBUILD,
		'default': '-i -I',
		'after': shlex.split,
	},
	{
		'name': 'apt-upgrade',
		'type': bool,
		'group': SBUILD,
		'default': True,
	},
	{
		'name': 'dry-run',
		'type': bool,
		'group': SBUILD,
		'default': False,
	},
	{
		'name': 'ignore-versions',
		'type': bool,
		'group': '',
		'default': False,
	},
]

class Cfg(object):
	def __init__(self, base=os.getcwd(), load=True):
		self.c = configparser.ConfigParser()
		self.cs = []
		self.loaded = set()
		self._overrides = {}

		if not load:
			return

		for f in DEFAULTS:
			self.load(f)

		self._load_tree(base)

	def _load_tree(self, base):
		paths = []
		curr = os.path.abspath(base)
		while len(curr) > 1:
			paths.insert(0, os.path.join(curr, '.debsrc'))
			curr = os.path.dirname(curr)

		for p in paths:
			self.load(p)

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
		cfg._overrides = self._overrides

		f = io.StringIO()
		self.c.write(f)
		cfg.load_string(f.getvalue())

		cfg._load_tree(path)

		return cfg

	def load(self, f):
		f = util.expand(f)[0]
		if not os.path.exists(f) or f in self.loaded:
			return

		self.loaded.add(f)
		self.c.read(f)

		c = configparser.ConfigParser()
		c.read(f)
		self.cs.append(c)

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

	def extra_sources(self, dist, release, arch):
		srcs = ''

		vs = [
			self._get_all(REPOS, 'extra-all', fallback=None),
			self._get_all(REPOS, 'extra-{}'.format(dist), fallback=None),
			self._get_all(REPOS, 'extra-{}-{}'.format(dist, arch), fallback=None),
			self._get_all(REPOS, 'extra-{}'.format(release), fallback=None),
			self._get_all(REPOS, 'extra-{}-{}'.format(release, arch), fallback=None),
		]
		for v in vs:
			if v:
				srcs += '\n'.join(v)
				srcs += '\n'

		srcs = srcs.format(
			DIST=dist,
			RELEASE=release)

		return util.to_set(srcs.splitlines())

	def extra_packages(self, dist, release, arch):
		pkgs = []

		vs = [
			self._get_all(PACKAGES, 'all', fallback=None),
			self._get_all(PACKAGES, '{}'.format(dist), fallback=None),
			self._get_all(PACKAGES, '{}-{}'.format(dist, arch), fallback=None),
			self._get_all(PACKAGES, '{}'.format(release), fallback=None),
			self._get_all(PACKAGES, '{}-{}'.format(release, arch), fallback=None),
		]

		pkgs = set()
		for v in vs:
			for p in v:
				pkgs.update(util.to_set(p.split(',')))

		return pkgs

	@property
	def env(self):
		env = {}
		for c in self.cs:
			if c.has_section('env'):
				env.update(dict(c.items('env')))

		return {k.upper(): v for k, v in env.items()}

def _gsetter(p):
	def getter(self):
		if p['name'] in self._overrides:
			return self._overrides[p['name']]

		if 'group' not in p:
			return p['default']

		t = p.get('type', None)

		fn = self.c.get
		if t is int:
			fn = self.c.getint
		elif t is bool:
			fn = self.c.getboolean
		elif t is set:
			def split(g, n, fallback=None):
				v = self.c.get(g, n, fallback=fallback)
				return util.to_set(v.split(','))
			fn = split

		v = fn(p['group'], p['name'], fallback=p['default'])

		if 'after' in p:
			v = p['after'](v)

		return v

	def setter(self, v):
		if 'after' in p:
			v = p['after'](v)
		self._overrides[p['name']] = v

	return getter, setter

for p in PROPS:
	getter, setter = _gsetter(p)
	setattr(Cfg,
		p['name'].replace('-', '_'),
		property(getter, setter))

class ConfigException(Exception):
	pass
