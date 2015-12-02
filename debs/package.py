import abc
import glob
import os.path
import re
import shutil

from . import run

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

	@abc.abstractmethod
	def gen_src(self, tmpdir):
		pass

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

	def gen_src(self, tmpdir):
		run.check('dpkg-source', '--build', self.path, cwd=tmpdir)
		return glob.glob('{}/*.dsc'.format(tmpdir))[0]

class _Quilt(_Native):
	def gen_src(self, tmpdir):
		self._clean()

		# Upstream version: debian versions are 1.2.3-DEB_REV, so remove
		# DEB_REV to get the upstream version
		upv = self.version.split('-')[0]

		tar = '{}_{}.orig.tar.xz'.format(self.name, upv)
		run.check('tar', 'cfJ', tar, '-C', self.path, '.', cwd=tmpdir)
		super().gen_src(tmpdir)

	def _clean(self):
		# The actual source is sometimes modified by patches. Just remove
		# them to keep things clean.
		try:
			run.check(
				'quilt',
				'pop', '-af',
				cwd=self.path)
		except run.RunException as e:
			# If no patches removed, exits with code 2
			if e.code != 2:
				raise

		shutil.rmtree('%s/.pc/' % self.path, ignore_errors=True)

class _Dsc(_Pkg):
	def __init__(self, path):
		super().__init__(path)
		self.name = self._get_key('Source', self.path)
		self.version = self._get_key('Version', self.path)

	def gen_src(self, tmpdir):
		pass

class InvalidPackage(Exception):
	def __init__(self, pkg, msg):
		super().__init__('{}: {}'.format(pkg, msg))
