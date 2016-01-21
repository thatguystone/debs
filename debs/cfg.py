import configparser
import copy
import io
import multiprocessing
import os
import os.path
import shlex

from . import consts, util

DEBSRC = '.debsrc'
DEFAULTS = [
	'/etc/debsrc',
	os.path.join(consts.CFG_DIR, 'debsrc'),
]

GROUP = 'debs'
PACKAGES = 'packages'
REPOS = 'repos'
SBUILD = 'sbuild'

# Values that are only relevant to a directory
DIR_ONLY = set([
	(GROUP, 'packages'),
])

PROPS = [
	{
		'name': 'refresh-after',
		'type': int,
		'group': GROUP,
		'default': 60*60*24*7,
	},
	{
		'name': 'packages',
		'type': util.OrderedSet,
		'group': GROUP,
		'default': '.',
		'dont_inherit': True,
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
		'type': util.OrderedSet,
		'group': GROUP,
		'default': 'all',
	},
	{
		'name': 'remotes',
		'type': util.OrderedSet,
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
		self._c = configparser.ConfigParser()
		self._base = os.path.abspath(base)
		self._cs = []
		self._loaded = set()
		self._overrides = {}

		if not load:
			return

		for f in DEFAULTS:
			self.load(f)

		self._load()

	def _load(self):
		paths = []
		top = self._base
		curr = top
		while len(curr) > 1:
			paths.insert(0, os.path.join(curr, DEBSRC))
			curr = os.path.dirname(curr)

		if os.path.isfile(top):
			top = os.path.dirname(top)

		for p in paths:
			if p != top:
				self._clear_path_local()
			self.load(p)

	def _clear_path_local(self):
		for do in DIR_ONLY:
			if do[0] in self._c:
				self._c.remove_option(do[0], do[1])

	def _get_all(self, group, key, fallback=None):
		res = []
		for c in self._cs:
			v = c.get(group, key, fallback=fallback)
			if v:
				res.append(v)

		return res

	def in_path(self, path):
		"""
		Get a new config object with any extra .debsrc files loaded from the
		given path and its parents.
		"""

		cfg = Cfg(base=path, load=False)
		cfg._cs = copy.copy(self._cs)
		cfg._loaded = copy.copy(self._loaded)
		cfg._overrides = copy.copy(self._overrides)

		for p in PROPS:
			if p.get('dont_inherit', False):
				cfg._overrides.pop(p['name'], None)

		f = io.StringIO()
		self._c.write(f)
		cfg.load_string(f.getvalue())

		cfg._load()

		return cfg

	def load(self, f):
		f = util.expand(f)[0]
		if not os.path.exists(f) or f in self._loaded:
			return

		self._loaded.add(f)
		self._c.read(f)

		c = configparser.ConfigParser()
		c.read(f)
		self._cs.append(c)

	def load_string(self, str):
		self._c.read_string(str)

		c = configparser.ConfigParser()
		c.read_string(str)
		self._cs.append(c)

	def main_mirror(self, dist, release):
		v = self._c.get(REPOS, release, fallback=None)
		if not v:
			v = self._c.get(REPOS, dist, fallback=None)

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

		pkgs = util.OrderedSet()
		for v in vs:
			for p in v:
				pkgs |= util.to_set(p.split(','))

		return pkgs

	def all_pkgs(self):
		pkgs = set()

		# `packages` expects to expand in directory that file lives in
		with util.push_dir(self._base):
			for pkg in self.packages:
				for p in util.expand(pkg):
					if p != self._base and os.path.exists(os.path.join(p, DEBSRC)):
						pkgs |= set(self.in_path(p).all_pkgs())
					else:
						pkgs.add((self.in_path(p), p))

		return sorted(pkgs, key=lambda c: c[1])

def _gsetter(p):
	def getter(self):
		if p['name'] in self._overrides:
			return self._overrides[p['name']]

		if 'group' not in p:
			return p['default']

		t = p.get('type', None)

		fn = self._c.get
		if t is int:
			fn = self._c.getint
		elif t is bool:
			fn = self._c.getboolean
		elif t is util.OrderedSet:
			def split(g, n, fallback=None):
				v = self._c.get(g, n, fallback=fallback)
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
