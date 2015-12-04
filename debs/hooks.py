import os.path

from . import run

def _dir(pkg):
	if os.path.isdir(pkg.path):
		return pkg.path
	return os.path.dirname(pkg.path)

def post_confirm(pkg):
	cmd = pkg.cfg.post_confirm
	if not cmd:
		return

	run.check(cmd,
		cwd=_dir(pkg),
		shell=True)
