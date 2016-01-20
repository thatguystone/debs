import abc
import glob
import logging
import os.path
import shutil

import debian.changelog
import debian.deb822

from . import run

log = logging.getLogger(__name__)

def load(path, cfg):
	path = os.path.abspath(path)

	if os.path.splitext(path)[1].lower() == '.dsc':
		return _Dsc(path, cfg)

	cl = os.path.join(path, 'debian', 'changelog')
	if not os.path.isfile(cl):
		_check_meant_dsc(path)
		raise InvalidPackage(path, 'missing debian/changelog')

	format = os.path.join(path, 'debian', 'source', 'format')
	if not os.path.isfile(format):
		raise InvalidPackage(path, 'missing debian/source/format')

	with open(format) as f:
		fmt = f.read()

	if '3.0 (quilt)' in fmt:
		return _Quilt(path, cfg)

	if '3.0 (native)' in fmt:
		return _Native(path, cfg)

	raise InvalidPackage(path, 'unsupported format: {}'.format(fmt))

def _check_meant_dsc(path):
	dscs = glob.glob(os.path.join(path, '*.dsc'))
	if dscs:
		log.info(
			'%s is not a valid path, but it contains a dsc; '
			'did you mean to use %s?',
				path,
				dscs[0])

class _Pkg(abc.ABC):
	@abc.abstractmethod
	def __init__(self, path, cfg):
		self.path = path
		self.cfg = cfg.in_path(self.path)

	@abc.abstractmethod
	def gen_src(self, tmpdir):
		pass

class _Native(_Pkg):
	def __init__(self, path, cfg):
		super().__init__(path, cfg)

		ctrl = os.path.join(self.path, 'debian', 'control')
		if not os.path.isfile(ctrl):
			raise InvalidPackage(self.path, 'missing {}'.format(ctrl))

		with open(ctrl) as f:
			cf = debian.deb822.Deb822(f)
			self.name = cf['Source']

		self._load_changelog()

	def _load_changelog(self):
		self.chglog = debian.changelog.Changelog()

		cl = os.path.join(self.path, 'debian', 'changelog')
		with open(cl) as f:
			try:
				self.chglog.parse_changelog(f, max_blocks=1)
			except debian.changelog.ChangelogParseError as e:
				raise InvalidPackage(self.path, e)

	@property
	def version(self):
		return self.chglog.full_version

	def gen_src(self, tmpdir):
		run.check('debian/rules', 'clean', cwd=self.path)
		run.check('dpkg-source', '-b',
			os.path.realpath(self.path), # dpkg-source doesn't like symlinks
			cwd=tmpdir)
		return glob.glob('{}/*.dsc'.format(tmpdir))[0]

class _Quilt(_Native):
	def gen_src(self, tmpdir):
		self._clean()

		tar = '{}_{}.orig.tar.xz'.format(
			self.name,
			self.chglog.upstream_version)

		run.check('tar',
			'cfJ', tar,
			'--force-local', # for when versions have a colon in them
			'-C', self.path,
			'.',
			cwd=tmpdir)

		return super().gen_src(tmpdir)

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
	def __init__(self, path, cfg):
		super().__init__(path, cfg)

		with open(self.path) as f:
			dsc = debian.deb822.Dsc(f)

			self.name = dsc['Source']
			self.version = dsc['Version']
			self.files = dsc.get('Files', [])

	def gen_src(self, tmpdir):
		srcdir = os.path.dirname(self.path)
		for f in self.files:
			src = os.path.join(srcdir, f['name'])
			shutil.copy(src, tmpdir)

		return shutil.copy(self.path, tmpdir)

class InvalidPackage(Exception):
	def __init__(self, pkg, msg):
		super().__init__('{}: {}'.format(pkg, msg))
