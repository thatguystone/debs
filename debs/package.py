import abc
import os.path
import re

CHANGELOG_VERSION = re.compile(r'.* \((.*)\) .*; urgency=')

def load(path):
	if os.path.splitext(path)[1].lower() == '.dsc':
		return _Dsc(path)

	cl = os.path.join(path, 'debian', 'changelog')
	if not os.path.isfile(cl):
		raise InvalidPackage(path, 'missing debian/changelog')

	format = os.path.join(path, 'debian', 'source', 'format')
	if not os.path.isfile(format):
		raise InvalidPackage(path, 'missing debian/source/format')

	with open(format) as f:
		fmt = f.read()

	if '3.0 (quilt)' in fmt:
		return _Quilt(path)

	if '3.0 (native)' in fmt:
		return _Native(path)

	raise InvalidPackage(path, 'unsupported format: {}'.format(fmt))

class _Pkg(abc.ABC):
	@abc.abstractmethod
	def __init__(self, path):
		self.path = path

	def _get_key(self, key, path):
		if not os.path.isfile(path):
			raise InvalidPackage(self.path, 'missing {}'.format(path))

		key = '{}: '.format(key.strip())
		with open(path) as f:
			for l in f:
				l = l.strip()
				if key in l:
					return l.split(':')[1].strip()

class _Native(_Pkg):
	def __init__(self, path):
		super().__init__(path)

		self.name = self._get_key(
			'Source',
			os.path.join(self.path, 'debian', 'control'))
		self._load_changelog()

	def _load_changelog(self):
		cl = os.path.join(self.path, 'debian', 'changelog')

		with open(cl) as f:
			m = CHANGELOG_VERSION.match(f.read())

		if not m:
			raise InvalidPackage(self.path,
				'could not find version in changelog')

		self.version = m.group(1)

class _Quilt(_Native):
	pass

class _Dsc(_Pkg):
	def __init__(self, path):
		super().__init__(path)
		self.name = self._get_key('Source', self.path)
		self.version = self._get_key('Version', self.path)

class InvalidPackage(Exception):
	def __init__(self, pkg, msg):
		super().__init__('{}: {}'.format(pkg, msg))
