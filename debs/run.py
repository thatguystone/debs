import logging
import os
import subprocess
import sys

log = logging.getLogger(__name__)

def _to_bytes(obj):
	if obj and isinstance(obj, str):
		obj = obj.encode("utf-8")
	return obj

def _to_str(b):
	return b.decode('utf-8').strip()

def get(*args):
	log.info('running %s', args)

	out = subprocess.check_output(args,
		stderr=subprocess.DEVNULL)

	return _to_str(out)

def check(*args, input=None, **kwargs):
	log.info('running %s', args)

	p = None
	try:
		if input:
			kwargs['stdin'] = subprocess.PIPE

		# Nose puts a StringIO instance as stdout, and that makes test output
		# ugly. Redirect as necessary.
		testing = sys.stdout != sys.__stdout__
		if testing and 'stdout' not in kwargs:
			kwargs['stdout'] = subprocess.PIPE
		if testing and 'stderr' not in kwargs:
			kwargs['stderr'] = subprocess.STDOUT

		if 'env' in kwargs:
			kwargs['env'] = os.environ.copy().update(kwargs['env'])

		p = subprocess.Popen(args, **kwargs)
		out = p.communicate(input=_to_bytes(input))

		if testing:
			print(_to_str(out[0]))

		if p.returncode != 0:
			raise RunException(p.returncode)
	finally:
		if p:
			p.wait()

def ignore(*args, **kwargs):
	try:
		check(*args, **kwargs)
	except Exception as e:
		log.info('ignoring run failure: %s', e)

def write(file, data):
	check('sudo', 'tee', file, input=data, stdout=subprocess.DEVNULL)

class RunException(Exception):
	def __init__(self, code):
		self.code = code

	def __str__(self):
		return 'Command exited with status: {}'.format(self.code)
