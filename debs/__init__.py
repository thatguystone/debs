import glob
import json
import logging
import os.path

from . import cfg, package, sbuild

__all__ = ['Debs']

logging.basicConfig(
	level=logging.INFO,
	format='%(levelname)-.1s: %(message)s')

class Debs(object):
	_VERSION_PATH = path = os.path.expanduser('~/.debs/versions')

	def __init__(self, dists=[], remotes=[], pkgs=[], extra_cfgs=[]):
		self.cfg = cfg.Cfg()
		for ecfg in extra_cfgs:
			cfg.load(ecfg)

		if dists:
			self.cfg.dists = set(dists)

		if remotes:
			self.cfg.remotes = set(remotes)

		if pkgs:
			self.cfg.packages = set(pkgs)

		self._load_versions()

		epkgs = []
		for pkg in self.cfg.packages:
			epkgs += util.expand(pkg)

		self.pkgs = []
		for epkg in epkgs:
			self.pkgs.append(package.load(epkg, self.cfg))

	def _load_versions(self):
		self.versions = {}

		if self.cfg.no_versions or not os.path.exists(self._VERSION_PATH):
			return

		try:
			with open(self._VERSION_PATH) as f:
				self.versions = json.load(f)
		except:
			# If this fails, don't stop the world
			pass

	def _save_versions(self):
		if self.cfg.no_versions:
			return

		with open(self._VERSION_PATH, 'w') as f:
			json.dump(self.versions, f, indent=4, sort_keys=True)

	def _version_key(self, pkg, env):
		return '{}[{}]'.format(pkg.name, env)

	def _show_build_summary(self):
		print('Going to build:')
		for pkg in self.pkgs:
			print()
			print('   `{}` (v{})'.format(pkg.name, pkg.version))
			print('      For:')
			for env in self.get_dists(pkg.cfg):
				skip = ''
				if self.skip_version(pkg, env):
					skip = ' (skip - already built)'
				print('         {}{}'.format(env, skip))
			print('      And upload to:')
			for r in self.get_remotes(pkg.cfg):
				print('         {}'.format(r))

	def _try_build(self, pkg, env):
		if self.skip_version(pkg, env):
			return

		ok = False
		while not ok:
			try:
				sbuild.build(pkg, env)
				ok = True
				self.versions[self._version_key(pkg, env)] = pkg.version
			except Exception as e:
				if not self.confirm('Build failed. Retry?', exit=False):
					raise

	def get_dists(self, cfg=None):
		if not cfg:
			cfg = self.cfg
		return sbuild.match(*cfg.dists)

	def get_remotes(self, cfg=None):
		if not cfg:
			cfg = self.cfg
		return dput.match(*cfg.remotes)

	def build(self):
		self._show_build_summary()
		self.confirm('Confirm?')

		for pkg in self.pkgs:
			for env in pkg.cfg.dists:
				self._try_build(pkg, env)

		self._save_versions()

	def skip_version(self, pkg, env):
		if self.cfg.ignore_versions:
			return False

		if self.cfg.no_versions:
			return False

		key = self._version_key(pkg, env)
		return self.versions.get(key, None) == pkg.version

	def confirm(self, msg, exit=True):
		print()

		if self.cfg.batch:
			return True

		res = input('{} [y/N] '.format(msg))
		if res and 'yes'.startswith(res.lower()):
			return True

		if exit:
			print('Aborting...')
			sys.exit(1)

		return False
