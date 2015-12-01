import getpass
import glob
import grp
import logging
import os.path
import pickle
import shutil
import sys

from . import dists, run

log = logging.getLogger(__name__)

# First run dpkg-source on the package from the tempdir, then run sbuild from the tempdir on the generated dsc. This should keep all files together!

DEFAULT_PKGS = [
	'build-essential',
	'eatmydata',
	'lintian',
]

SUFFIX = '-debs'

if getpass.getuser() != 'root' and getpass.getuser() not in grp.getgrnam('sbuild').gr_mem:
	log.error('Current user (%s) not in sbuild group. Adding...', getpass.getuser())
	run.check('sudo', 'sbuild-adduser', getpass.getuser())
	log.error('You need to log out and log back in before you can use sbuild.')
	sys.exit(1)

def _dir(release, arch):
	return '/var/lib/debs/{}-{}'.format(release, arch)

def _cfg_file(release, arch):
	return glob.glob('/etc/schroot/chroot.d/{}-{}-debs-*'.format(release, arch))[0]

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
			release,
			dir,
			dists.main_mirror(release, cfg=cfg))

		_reconfig(cfg, release, arch)
	except:
		delete(release, arch)
		raise

def _reconfig(cfg, release, arch):
	dir = _dir(release, arch)
	p = os.path.join(dir, '.debscfg')

	c = {}
	cs = None
	if os.path.exists(p):
		with open(p, 'rb') as f:
			cs = f.read()
		c = pickle.loads(cs)

	_check_cfg_has(release, arch, 'union-type=overlay\n')
	_reconfig_mirrors(release, arch, cfg, dir)
	_reconfig_pkgs(release, arch, cfg, c)
	_check_cfg_has(release, arch, 'command-prefix=eatmydata\n')

	ncs = pickle.dumps(c)
	if ncs != cs:
		run.write(p, ncs)

def _check_cfg_has(release, arch, line):
	cfgf = _cfg_file(release, arch)

	with open(cfgf) as f:
		cfg = f.read()

	if not cfg.endswith('\n'):
		cfg += '\n'

	if not line.endswith('\n'):
		line += '\n'

	if line not in cfg:
		cfg += line
		run.write(cfgf, cfg)

def _reconfig_mirrors(release, arch, cfg, dir):
	srcs = os.path.join(dir, 'etc', 'apt', 'sources.list')

	with open(srcs) as f:
		have = f.read()

	want = dists.sources(release, cfg=cfg)

	if want != have:
		run.write(srcs, want)
		_update(release, arch)

def _reconfig_pkgs(release, arch, cfg, c):
	have = set(c.get('pkgs', []))
	want = dists.packages(release, cfg=cfg).union(set(DEFAULT_PKGS))

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

def _update(release, arch):
	_run_in_chroot(release, arch, 'apt-get', 'update')

def delete(release, arch):
	run.ignore('sudo', 'rm', '-rf', _dir(release, arch))
	run.ignore('sudo', 'rm', '-rf', _cfg_file(release, arch))

def installed():
	envs = set()

	scs = run.get('schroot', '-l', '--all-source-chroots').split('\n')
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
	ds = dists.match(*specs, installed=inst)

	if only_installed:
		ds = ds.intersection(inst)

	return sorted(ds)

def ensure(cfg, *envs):
	"""
	Ensure that an sbuild environment for the given release-arch environments
	exist.
	"""

	inst = installed()
	for env in envs:
		release, arch = env.split('-')

		if env in inst:
			_reconfig(cfg, release, arch)
		else:
			_create(cfg, release, arch)

def build(cfg, env, dsc, tmpdir):
	pass

class SbuildException(Exception):
	pass
