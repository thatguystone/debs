import configparser
import os
import os.path

DEFAULTS = [
	'/etc/debsrc',
	'~/.debsrc',
]

GROUP = 'debs'
REPOS_GROUP = 'repos'

class Cfg(object):
	def __init__(self, base=os.getcwd()):
		self.c = configparser.ConfigParser()
		self.cs = []

		for f in DEFAULTS:
			self._load(f)

		paths = []
		curr = base
		while curr != '/':
			paths.insert(0, os.path.join(curr, '.debsrc'))
			curr = os.path.dirname(curr)

		for p in paths:
			self._load(p)

	def _load(self, f):
		if not os.path.exists(f):
			return

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

	def load_string(self, str):
		self.c.read_string(str)

		c = configparser.ConfigParser()
		c.read_string(str)
		self.cs.append(c)

	def main_mirror(self, dist, release):
		v = self.c.get(REPOS_GROUP, release, fallback=None)
		if not v:
			v = self.c.get(REPOS_GROUP, dist, fallback=None)

		return v

	def extra_sources(self, dist, release):
		srcs = ''

		vs = [
			self._get_all(REPOS_GROUP, 'extras-' + dist, fallback=None),
			self._get_all(REPOS_GROUP, 'extras-' + release, fallback=None),
		]
		for v in vs:
			if v:
				srcs += '\n'.join(v)
				srcs += '\n'

		srcs = srcs.format(
			DIST=dist,
			RELEASE=release)

		return srcs.strip()

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

		return set(pkgs)

class ConfigException(Exception):
	pass
