import glob
import json
import logging
import os.path
import sys

from . import cfg, package, sbuild

__all__ = ['Debs']

log = logging.getLogger(__name__)

class Debs(object):
	_VERSION_PATH = path = os.path.expanduser('~/.debs/versions')

	def __init__(self, envs=[], remotes=[], pkgs=[], extra_cfgs=[]):
		self.cfg = cfg.Cfg()
		for ecfg in extra_cfgs:
			cfg.load(ecfg)

		if envs:
			self.cfg.envs = set(envs)

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

	def _show_prebuild_summary(self):
		print('Going to build:')
		for pkg in self.pkgs:
			print()
			print('   `{}` (v{})'.format(pkg.name, pkg.version))
			print('      For:')
			for env in self.get_envs(cfg=pkg.cfg):
				skip = ''
				if self._skip_version(pkg, env):
					skip = ' (skip - already built)'
				print('         {}{}'.format(env, skip))
			print('      And upload to:')
			for r in self.get_remotes(pkg.cfg):
				print('         {} ({})'.format(r[0], r[1]))

	def _try_build(self, pkg, env):
		if self._skip_version(pkg, env):
			return

		ok = False
		while not ok:
			try:
				uploaded = sbuild.build(pkg, env)
				ok = True
				if uploaded:
					self.versions[self._version_key(pkg, env)] = pkg.version
			except Exception as e:
				if not self._confirm('Build failed. Retry?',
					exit=False,
					allow_batch=False):
					raise

	def _skip_version(self, pkg, env):
		if self.cfg.ignore_versions:
			return False

		if self.cfg.no_versions:
			return False

		key = self._version_key(pkg, env)
		return self.versions.get(key, None) == pkg.version

	def _confirm(self, msg, exit=True, allow_batch=True):
		print()

		if self.cfg.batch:
			return allow_batch

		res = input('{} [y/N] '.format(msg)).strip()
		if res and 'yes'.startswith(res.lower()):
			return True

		if exit:
			print('Aborting...')
			sys.exit(1)

		return False

	def get_envs(self, *envs, only_installed=False, cfg=None):
		if not cfg:
			cfg = self.cfg

		envs = list(filter(None, envs))
		if not envs:
			envs = cfg.envs
		return sbuild.match(*envs, only_installed=only_installed)

	def get_remotes(self, *remotes, cfg=None):
		if not cfg:
			cfg = self.cfg

		remotes = list(filter(None, remotes))
		if not remotes:
			remotes = cfg.remotes
		return dput.match(*remotes)

	def build(self):
		self._show_prebuild_summary()
		self._confirm('Confirm?')

		for pkg in self.pkgs:
			for env in self.get_envs(cfg=pkg.cfg):
				self._try_build(pkg, env)

		self._save_versions()

	def delete(self):
		envs = self.get_envs(cfg=self.cfg, only_installed=True)
		if not envs:
			log.error('No matching envs are installed.')
			return

		print('Going to delete:')
		for env in envs:
			print('   `{}`'.format(env))

		self._confirm('Confirm?')

		for env in self.envs:
			sbuild.delete(env)

