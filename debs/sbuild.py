import getpass
import glob
import grp
import logging
import os
import os.path
import pickle
import shutil
import sys
import tempfile
import time

from . import envs, dput, run, util

log = logging.getLogger(__name__)

DEFAULT_PKGS = [
	'build-essential',
	'ccache',
	'eatmydata',
	'lintian',
	'debhelper',
]

CCACHE_DIR = '/var/cache/ccache-sbuild'

SUFFIX = '-debs'

def _preconfigure():
	# Share apt archive cache
	_check_file_has(
		'/etc/schroot/sbuild/fstab',
		'/var/cache/apt/archives',
		rest=' /var/cache/apt/archives	none rw,bind	0	0',
		ignore_missing=True)

	_check_ccache()
	_check_user_in_group()

def _check_ccache():
	if not os.path.exists(CCACHE_DIR):
		run.check(
			'sudo',
			'install',
			'--compare',
			'--group=sbuild',
			'--mode=2775', # Inherit sbuild group
			'-d', CCACHE_DIR)

	# Share ccache stuffs
	_check_file_has(
		'/etc/schroot/sbuild/fstab',
		'{}'.format(CCACHE_DIR),
		rest='	{}	none rw,bind	0	0'.format(CCACHE_DIR),
		ignore_missing=True)

	_check_file_is(
		os.path.join(CCACHE_DIR, 'ccache.conf'),
		util.strip_lines('''
		cache_dir = {DIR}
		umask = 002
		hard_link = false
		compression = true
		'''.format(
			DIR=CCACHE_DIR)))

	_check_file_is(
		os.path.join(CCACHE_DIR, 'env'),
		util.strip_lines('''#! /bin/bash
		export CCACHE_DIR={}
		export PATH="/usr/lib/ccache:$PATH"
		exec "$@"
		'''.format(CCACHE_DIR)),
		executable=True)

def _check_user_in_group():
	u = getpass.getuser()
	if u != 'root' and u not in grp.getgrnam('sbuild').gr_mem:
		log.error('Current user (%s) not in sbuild group. Adding...', u)
		run.check('sudo', 'adduser', u, 'sbuild')
		log.error('You need to log out and log back in before you can use sbuild.')

		if not os.getenv('CI'):
			sys.exit(1)

def _dir(release, arch):
	return '/var/lib/debs/{}-{}'.format(release, arch)

def _cfg_file(release, arch):
	f = '/etc/schroot/chroot.d/{}-{}-debs-*'.format(release, arch)
	gs = glob.glob(f)
	if gs:
		return gs[0]
	return f

def _schroot_name(release, arch, source=False):
	name = '{}-{}{}'.format(release, arch, SUFFIX)
	if source:
		name = 'source:{}'.format(name)

	return name

def _run_in_chroot(release, arch, *args):
	run.check(
		'sudo',
		'schroot',
		'-c', _schroot_name(release, arch, source=True),
		'--directory', '/root',
		'--', *args)

def _create(cfg, release, arch):
	dir = _dir(release, arch)
	if os.path.exists(dir):
		raise SbuildException(
			'Cowardly refusing to create '
			'{}-{} in existing dir: {}'.format(release, arch, dir))

	try:
		run.check('sudo', 'mkdir', '-p', dir)

		run.check(
			'sudo',
			'sbuild-createchroot',
			'--chroot-suffix={}'.format(SUFFIX),
			'--arch={}'.format(arch),
			'--components={}'.format(envs.components(release, sep=',')),
			release,
			dir,
			envs.main_mirror(release, cfg=cfg))

		_reconfig(cfg, release, arch)
	except:
		_delete(release, arch)
		raise

def _reconfig(cfg, release, arch):
	dir = _dir(release, arch)
	p = os.path.join(dir, '.debscfg')

	c = {}
	cs = None
	lastmod = -1
	if os.path.exists(p):
		with open(p, 'rb') as f:
			cs = f.read()
		c = pickle.loads(cs)
		lastmod = os.path.getmtime(p)

	_check_cfg_has(release, arch, 'union-type=', 'overlay')
	_reconfig_mirrors(release, arch, cfg, dir)
	_reconfig_pkgs(release, arch, cfg, c)
	_check_cfg_has(release, arch,
		'command-prefix=',
		'{}/env,eatmydata'.format(CCACHE_DIR))

	upgraded = False
	if lastmod != -1:
		upgraded = _check_upgrade(cfg, lastmod, release, arch)

	ncs = pickle.dumps(c)
	if ncs != cs or upgraded:
		run.write(p, ncs)

def _check_cfg_has(release, arch, pfx, rest):
	_check_file_has(_cfg_file(release, arch), pfx, rest)

def _reconfig_mirrors(release, arch, cfg, dir):
	srcs = os.path.join(dir, 'etc', 'apt', 'sources.list')

	if not _check_file_is(srcs, envs.sources(release, arch, cfg=cfg)):
		_update(release, arch)

def _check_file_has(path, pfx, rest, ignore_missing=False):
	if ignore_missing and not os.path.exists(path):
		return

	with open(path) as f:
		contents = f.read()

	if not contents.endswith('\n'):
		contents += '\n'

	complete = pfx + rest
	if not complete.endswith('\n'):
		complete += '\n'

	if complete in contents:
		return

	lines = contents.splitlines()
	for i, l in enumerate(lines):
		if l.startswith(pfx):
			lines[i] = complete.strip()
			break
	else:
		lines.append(complete.strip())

	out = '\n'.join(lines) + '\n'
	run.write(path, out)

def _check_file_is(path, contents, executable=False):
	have = ''
	if os.path.exists(path):
		with open(path) as f:
			have = f.read()

	had = contents == have
	if not had:
		run.write(path, contents)

	if executable and not had:
		run.check('sudo', 'chmod', '+x', path)

	return had

def _reconfig_pkgs(release, arch, cfg, c):
	have = set(c.get('pkgs', []))
	want = envs.packages(release, arch, cfg=cfg) | set(DEFAULT_PKGS)

	if have != want:
		rm = have - want
		if rm:
			_run_in_chroot(release, arch,
				'apt-get',
				'remove', *rm)

		inst = want - have
		if inst:
			_run_in_chroot(release, arch,
				'apt-get',
				'-y', '--force-yes',
				'install', *inst)

	c['pkgs'] = sorted(want)

def _check_upgrade(cfg, lastmod, release, arch):
	now = time.time()
	age = now - lastmod

	if age < cfg.refresh_after:
		return False

	log.info('%s-%s out of date; upgrading...', release, arch)
	run.check(
		'sudo',
		'sbuild-update',
		'-udcar',
		_schroot_name(release, arch))

	return True

def _update(release, arch):
	run.check(
		'sudo',
		'sbuild-update',
		'-u',
		_schroot_name(release, arch))

def _make_sbuildrc(cfg, path):
	require = None
	curr = os.getenv('SBUILD_CONFIG')
	if curr:
		curr = os.path.abspath(curr)
		if os.path.exists(curr):
			require = curr

	with open(path, 'w') as f:
		if require:
			f.write('require "{}";\n'.format(require))

		if cfg.key:
			f.write('$key_id = "{}";\n'.format(cfg.key))

		f.write(util.strip_lines('''
			$run_lintian = {LINTIAN};
			$lintian_opts = {LINTIAN_OPTS};

			$apt_update = {APT_UPGRADE};
			$apt_distupgrade = {APT_UPGRADE};

			1;
			'''.format(
				LINTIAN=int(cfg.lintian),
				LINTIAN_OPTS=cfg.lintian_args,
				APT_UPGRADE=int(cfg.apt_upgrade),
			)))

def _delete(release, arch):
	name = _schroot_name(release, arch)

	run.ignore('sudo', 'schroot',
		'--end-session', '--all-sessions',
		'chroot:{}'.format(name))
	run.ignore('sudo', 'schroot',
		'--end-session', '--all-sessions',
		'source:{}'.format(name))
	run.ignore('sudo', 'rm', '-rf', _dir(release, arch))
	run.ignore('sudo', 'rm', '-rf', _cfg_file(release, arch))

def delete(env):
	release, arch = envs.split(env)
	_delete(release, arch)

def installed():
	envs = set()

	scs = run.get('schroot', '-l', '--all-source-chroots').splitlines()
	for sc in filter(lambda s: SUFFIX in s, scs):
		envs.add(sc
			.replace('source:', '')
			.replace(SUFFIX, ''))

	return sorted(envs)

def match(*specs, only_installed=False):
	"""
	Find all sbuild environments matching the given specs.
	"""

	inst = set(installed())
	ds = envs.match(*specs, installed=inst)

	if only_installed:
		ds = ds.intersection(inst)

	return sorted(ds)

def ensure(cfg, *envss):
	"""
	Ensure that an sbuild environment for the given release-arch environments
	exist.
	"""

	inst = installed()
	for env in envss:
		release, arch = envs.split(env)

		if env in inst:
			_reconfig(cfg, release, arch)
		else:
			_create(cfg, release, arch)

def build(pkg, env, remotes=[]):
	"""
	Build the given package for in the given environment. Return if the
	package was uploaded anywhere.
	"""

	cfg = pkg.cfg

	if not cfg.dry_run:
		ensure(cfg, env)

	release, arch = envs.split(env)

	tmpdir = tempfile.mkdtemp(prefix='debs-')
	sbuildrc = os.path.join(tmpdir, '.sbuildrc')
	try:
		dsc = pkg.gen_src(tmpdir)
		_make_sbuildrc(cfg, sbuildrc)

		if cfg.dry_run:
			return

		args = []
		if cfg.user:
			args += ['sudo']

			if cfg.user_keep_env:
				args += ['-E']

			args += ['-u', cfg.user]

		args += [
			'sbuild',
			'--arch-all',
			'-j', str(cfg.jobs),
			'--dist', release,
			'--chroot', _schroot_name(release, arch),
		]

		if cfg.include_src:
			args.append('--source')

		args.append(dsc)

		run.check(
			*args,
			cwd=tmpdir,
			env={
				'SBUILD_CONFIG': sbuildrc,
			})

		chgs = glob.glob(os.path.join(tmpdir, '*.changes'))[0]
		for r in remotes:
			dput.put(r, chgs)
	finally:
		shutil.rmtree(tmpdir, ignore_errors=True)

class SbuildException(Exception):
	pass

_preconfigure()
